import base64
import inspect
import json
from unittest.mock import MagicMock, patch

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
        result = run_sql_query(query="SELECT id, name FROM widgets", user_id="user-123", max_rows=2)

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
        result = run_sql_query(query="SELECT id, name FROM widgets WHERE 1=0", user_id="user-123")

    assert result.columns == ["id", "name"]
    assert result.rows == []
    assert result.row_count == 0
    assert result.message == "Query executed successfully but returned no rows."


def test_run_sql_query_rejects_write_before_touching_database(monkeypatch):
    monkeypatch.setenv("SQL_CONNECTION_STRING", "SERVER=test;Encrypt=yes")
    with patch("mcp_server.sql_connection.connect") as mock_connect:
        with pytest.raises(ToolError, match="only accepts SELECT/WITH"):
            run_sql_query(query="DELETE FROM widgets", user_id="user-123")

    mock_connect.assert_not_called()


def test_run_sql_query_requires_connection_string_env_var(monkeypatch):
    monkeypatch.delenv("SQL_CONNECTION_STRING", raising=False)

    with pytest.raises(ToolError, match="SQL_CONNECTION_STRING is not set"):
        run_sql_query(query="SELECT 1", user_id="user-123")


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


def test_generate_report_has_no_output_path_parameter():
    assert "output_path" not in inspect.signature(generate_report).parameters
