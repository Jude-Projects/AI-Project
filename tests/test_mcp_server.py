import base64
import inspect
import json
import os
import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import anyio
import pytest
from mcp.server.mcpserver.exceptions import ResourceError, ToolError

import mcp_server
from mcp_server import (
    _validate_identifier,
    _validate_read_only,
    describe_table,
    generate_report,
    list_database_tables,
    run_sql_query,
)


def call_tool(name, arguments):
    return anyio.run(mcp_server.mcp.call_tool, name, arguments)


def read_resource(uri):
    return anyio.run(mcp_server.mcp.read_resource, uri)


async def _acall(fn, **kwargs):
    return await fn(**kwargs)


def call_async(fn, **kwargs):
    """Run an async tool function directly (bypassing mcp.call_tool's schema
    layer) with keyword arguments - for tests exercising the function's own
    logic against mocks, same as before these tools became async."""
    return anyio.run(lambda: _acall(fn, **kwargs))


@pytest.mark.parametrize(
    "query",
    [
        "SELECT * FROM widgets",
        "  select id from widgets",
        "WITH cte AS (SELECT 1 AS x) SELECT * FROM cte",
    ],
)
def test_validate_read_only_accepts_select_and_with(query):
    assert _validate_read_only(query) == query.strip()


@pytest.mark.parametrize(
    "query",
    [
        "DELETE FROM widgets",
        "DROP TABLE widgets",
        "INSERT INTO widgets VALUES (1)",
        "UPDATE widgets SET x = 1",
    ],
)
def test_validate_read_only_rejects_non_select(query):
    with pytest.raises(ToolError, match="only accepts SELECT/WITH"):
        _validate_read_only(query)


def test_validate_read_only_rejects_stacked_statements():
    with pytest.raises(ToolError, match="multiple statements"):
        _validate_read_only("SELECT 1; DROP TABLE widgets")


@pytest.mark.parametrize("name", ["widgets", "Widget_1", "widgets2"])
def test_validate_identifier_accepts_simple_names(name):
    assert _validate_identifier(name) == name


@pytest.mark.parametrize(
    "name", ["widgets; DROP TABLE x", "widgets'", "my table", "widgets--"]
)
def test_validate_identifier_rejects_unsafe_names(name):
    with pytest.raises(ResourceError, match="Invalid table name"):
        _validate_identifier(name)


def test_run_sql_query_happy_path(monkeypatch):
    monkeypatch.setenv("SQL_CONNECTION_STRING", "SERVER=test;Encrypt=yes")
    mock_conn = MagicMock()
    with patch("mcp_server.sql_connection.connect", return_value=mock_conn) as mock_connect, patch(
        "mcp_server.sql_connection.execute_query",
        return_value=(["id", "name"], [(1, "a"), (2, "b"), (3, "c")]),
    ) as mock_execute:
        result = call_async(run_sql_query, query="SELECT id, name FROM widgets", user_id="user-123", max_rows=2)

    mock_connect.assert_called_once_with("SERVER=test;Encrypt=yes")
    mock_execute.assert_called_once_with(
        mock_conn, "SELECT id, name FROM widgets", "user-123", with_columns=True
    )
    mock_conn.close.assert_called_once()
    assert result.columns == ["id", "name"]
    assert result.rows == [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]
    assert result.row_count == 2
    assert result.message is None


def test_run_sql_query_returns_structured_empty_result_on_no_rows(monkeypatch):
    monkeypatch.setenv("SQL_CONNECTION_STRING", "SERVER=test;Encrypt=yes")
    mock_conn = MagicMock()
    with patch("mcp_server.sql_connection.connect", return_value=mock_conn), patch(
        "mcp_server.sql_connection.execute_query",
        return_value=(["id", "name"], []),
    ):
        result = call_async(run_sql_query, query="SELECT id, name FROM widgets WHERE 1=0", user_id="user-123")

    assert result.columns == ["id", "name"]
    assert result.rows == []
    assert result.row_count == 0
    assert result.message == "Query executed successfully but returned no rows."


def test_run_sql_query_rejects_write_before_touching_database(monkeypatch):
    monkeypatch.setenv("SQL_CONNECTION_STRING", "SERVER=test;Encrypt=yes")
    with patch("mcp_server.sql_connection.connect") as mock_connect:
        with pytest.raises(ToolError, match="only accepts SELECT/WITH"):
            call_async(run_sql_query, query="DELETE FROM widgets", user_id="user-123")

    mock_connect.assert_not_called()


def test_run_sql_query_requires_connection_string_env_var(monkeypatch):
    monkeypatch.delenv("SQL_CONNECTION_STRING", raising=False)

    with pytest.raises(ToolError, match="SQL_CONNECTION_STRING is not set"):
        call_async(run_sql_query, query="SELECT 1", user_id="user-123")


def test_list_database_tables_maps_rows_to_named_dicts(monkeypatch):
    monkeypatch.setenv("SQL_CONNECTION_STRING", "SERVER=test;Encrypt=yes")
    mock_conn = MagicMock()
    with patch("mcp_server.sql_connection.connect", return_value=mock_conn), patch(
        "mcp_server.sql_connection.execute_query",
        return_value=[("dbo", "widgets", "BASE TABLE")],
    ):
        result = list_database_tables()

    assert result == [{"schema": "dbo", "table": "widgets", "type": "BASE TABLE"}]
    mock_conn.close.assert_called_once()


def test_describe_table_rejects_unsafe_identifier_before_querying():
    with patch("mcp_server.sql_connection.connect") as mock_connect:
        with pytest.raises(ResourceError, match="Invalid table name"):
            describe_table("widgets; DROP TABLE x")

    mock_connect.assert_not_called()


def test_describe_table_raises_when_table_not_found(monkeypatch):
    monkeypatch.setenv("SQL_CONNECTION_STRING", "SERVER=test;Encrypt=yes")
    mock_conn = MagicMock()
    with patch("mcp_server.sql_connection.connect", return_value=mock_conn), patch(
        "mcp_server.sql_connection.execute_query", return_value=[]
    ):
        with pytest.raises(ResourceError, match="No table named"):
            describe_table("does_not_exist")

    mock_conn.close.assert_called_once()


def test_list_report_formats_returns_supported_formats():
    result = read_resource("report://formats")
    assert json.loads(result[0].content) == ["pdf", "text"]
    assert result[0].mime_type == "application/json"


def test_generate_report_happy_path_text():
    result = call_tool(
        "generate_report",
        {
            "report_format": "text",
            "results": {"metric": "revenue", "aggregation": "sum", "value": 45231.5},
            "user_id": "user-123",
        },
    )

    assert result.is_error is False
    decoded = base64.b64decode(result.structured_content["content_base64"])
    assert decoded == b"The total revenue is 45,231.50."
    assert result.structured_content["report_format"] == "text"
    assert result.structured_content["byte_size"] == len(decoded)


def test_generate_report_happy_path_pdf_with_breakdown():
    result = call_tool(
        "generate_report",
        {
            "report_format": "pdf",
            "results": {
                "metric": "orders",
                "aggregation": "count",
                "value": 150,
                "breakdown": [
                    {"label": "widgets", "value": 90},
                    {"label": "gadgets", "value": 60},
                ],
            },
            "user_id": "user-123",
        },
    )

    assert result.is_error is False
    decoded = base64.b64decode(result.structured_content["content_base64"])
    assert decoded.startswith(b"%PDF")


def test_generate_report_rejects_unsupported_format():
    # Rejected at the schema layer (Literal["pdf", "text"]) before the tool
    # body runs, so mcp.call_tool() raises rather than returning is_error=True
    # (that wrapping only happens at the wire-protocol handler, not this
    # lower-level call used directly in tests).
    with pytest.raises(ToolError, match="csv"):
        call_tool(
            "generate_report",
            {
                "report_format": "csv",
                "results": {"metric": "revenue", "aggregation": "sum", "value": 1},
                "user_id": "user-123",
            },
        )


def test_generate_report_propagates_language_barrier_error_for_non_ascii_metric():
    # Non-ASCII metric names aren't blocked by ReportResults' schema (metric
    # is just `str`) - this exercises explanation_generator's own domain
    # validation raised from inside the tool body, same "any exception
    # becomes a clean error" propagation path as run_sql_query's errors,
    # just surfaced as a raised exception rather than is_error=True at this
    # call level.
    with pytest.raises(ToolError, match="non-ASCII characters"):
        call_tool(
            "generate_report",
            {
                "report_format": "text",
                "results": {"metric": "収益", "aggregation": "sum", "value": 1},
                "user_id": "user-123",
            },
        )


def _make_ctx_with_roots(root_paths):
    """A minimal stand-in for a live-request Context: real enough for
    _resolve_within_roots (_request_context truthy, .session.list_roots()
    returning the given roots, .log callable) without standing up the
    full SDK request machinery."""
    ctx = MagicMock()
    ctx._request_context = MagicMock()
    roots = [MagicMock(uri=Path(p).resolve().as_uri()) for p in root_paths]
    ctx.session.list_roots = AsyncMock(return_value=MagicMock(roots=roots))
    ctx.log = AsyncMock()
    return ctx


def resolve_within_roots(ctx, correlation_id, tool, requested_path):
    return anyio.run(
        lambda: mcp_server._resolve_within_roots(ctx, correlation_id, tool, requested_path)
    )


def test_resolve_within_roots_allows_path_inside_declared_root(tmp_path):
    ctx = _make_ctx_with_roots([tmp_path])

    resolved = resolve_within_roots(ctx, "corr-1", "generate_report", str(tmp_path / "report.pdf"))

    assert resolved == (tmp_path / "report.pdf").resolve()
    ctx.log.assert_not_called()


def test_resolve_within_roots_denies_dot_dot_traversal(tmp_path):
    allowed_root = tmp_path / "allowed"
    allowed_root.mkdir()
    ctx = _make_ctx_with_roots([allowed_root])
    escape_path = str(allowed_root / ".." / "escape.pdf")

    with pytest.raises(ToolError, match="resolves outside every root"):
        resolve_within_roots(ctx, "corr-1", "generate_report", escape_path)

    ctx.log.assert_awaited_once()
    logged_data = ctx.log.await_args.args[1]
    assert logged_data["event"] == "access_denied"
    assert logged_data["reason"] == "path_outside_allowed_roots"
    assert logged_data["requested_path"] == escape_path


def test_resolve_within_roots_denies_sibling_directory_sharing_a_string_prefix(tmp_path):
    # The exact case a naive str.startswith(root) check gets wrong:
    # "reports-secret" starts with the string "reports" without being
    # inside it - a real path-component comparison must still deny this.
    allowed_root = tmp_path / "reports"
    allowed_root.mkdir()
    ctx = _make_ctx_with_roots([allowed_root])
    sibling_path = str(tmp_path / "reports-secret" / "x.pdf")

    with pytest.raises(ToolError, match="resolves outside every root"):
        resolve_within_roots(ctx, "corr-1", "generate_report", sibling_path)


def _make_reparse_point(link: Path, target: Path) -> bool:
    """A real directory symlink where the OS grants the privilege (needs
    Developer Mode or elevation on Windows); otherwise a junction point
    (no special privilege required on Windows NTFS) - Path.resolve()
    follows either identically, and both are the same class of attack:
    a filesystem reparse point whose literal path looks contained but
    whose real target is not. Returns False only if neither works."""
    try:
        link.symlink_to(target, target_is_directory=True)
        return True
    except OSError:
        pass
    if os.name == "nt":
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            capture_output=True, text=True,
        )
        return result.returncode == 0
    return False


def test_resolve_within_roots_denies_symlink_escape(tmp_path):
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    allowed_root = tmp_path / "allowed"
    allowed_root.mkdir()
    link = allowed_root / "link"
    if not _make_reparse_point(link, outside_dir):
        pytest.skip("neither symlinks nor junctions are permitted in this environment")

    ctx = _make_ctx_with_roots([allowed_root])
    escape_path = str(link / "secret.pdf")

    with pytest.raises(ToolError, match="resolves outside every root"):
        resolve_within_roots(ctx, "corr-1", "generate_report", escape_path)


def test_resolve_within_roots_denies_when_client_declares_no_roots(tmp_path):
    ctx = _make_ctx_with_roots([])

    with pytest.raises(ToolError, match="resolves outside every root"):
        resolve_within_roots(ctx, "corr-1", "generate_report", str(tmp_path / "report.pdf"))


def test_generate_report_writes_to_disk_inside_declared_root(tmp_path, monkeypatch):
    monkeypatch.setenv("SQL_CONNECTION_STRING", "SERVER=test;Encrypt=yes")
    ctx = _make_ctx_with_roots([tmp_path])
    output_path = str(tmp_path / "report.txt")

    result = call_async(
        generate_report,
        report_format="text",
        results=mcp_server.ReportResults(metric="revenue", aggregation="sum", value=1),
        user_id="user-123",
        output_path=output_path,
        ctx=ctx,
    )

    assert result.written_to == str(Path(output_path).resolve())
    assert Path(output_path).read_bytes() == base64.b64decode(result.content_base64)


def test_generate_report_denies_output_path_outside_declared_root(tmp_path):
    allowed_root = tmp_path / "allowed"
    allowed_root.mkdir()
    ctx = _make_ctx_with_roots([allowed_root])
    outside_path = str(tmp_path / "escape.txt")

    with pytest.raises(ToolError, match="resolves outside every root"):
        call_async(
            generate_report,
            report_format="text",
            results=mcp_server.ReportResults(metric="revenue", aggregation="sum", value=1),
            user_id="user-123",
            output_path=outside_path,
            ctx=ctx,
        )

    assert not Path(outside_path).exists()
