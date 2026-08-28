"""MCP server exposing the AI Data Assistant's SQL Server layer
(sql_connection.py) to a conversational model, read-only.

Serves REQ-001/REQ-011/REQ-014/REQ-015 (STORY-001) by making the
already-verified connect()/execute_query() layer reachable over MCP,
without granting the model write access or connection control."""

import base64
import os
import re
from pathlib import Path
from typing import Annotated, Literal

from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ResourceError, ToolError
from pydantic import BaseModel, Field

import report_generator
import sql_connection
from explanation_generator import (
    ComplexityOverloadError,
    LanguageBarrierError,
    MisinterpretationError,
)
from report_generator import (
    DataExportError,
    PermissionDeniedError,
    UnsupportedFormatError,
)

REPORT_ERRORS = (
    UnsupportedFormatError,
    DataExportError,
    PermissionDeniedError,
    MisinterpretationError,
    ComplexityOverloadError,
    LanguageBarrierError,
)

# Resolve .env relative to this file, not the process's current working
# directory - load_dotenv()'s default cwd-search is unreliable once this
# server is launched by an MCP client (e.g. Claude Code) from an
# unpredictable working directory rather than always from the repo root.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

mcp = MCPServer("ai-data-assistant-sql")

IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")
READ_ONLY_KEYWORDS = {"select", "with"}


def _connection_string() -> str:
    value = os.environ.get("SQL_CONNECTION_STRING")
    if not value:
        raise ToolError(
            "SQL_CONNECTION_STRING is not set. Add it to .env (see .env.example)."
        )
    return value


def _get_connection() -> "sql_connection.pyodbc.Connection":
    return sql_connection.connect(_connection_string())


def _validate_identifier(name: str) -> str:
    if not IDENTIFIER_PATTERN.match(name):
        raise ResourceError(
            f"Invalid table name {name!r}: only letters, digits, and "
            "underscores are allowed."
        )
    return name


def _validate_read_only(query: str) -> str:
    stripped = query.strip()
    first_word = stripped.split(None, 1)[0].lower().strip("(") if stripped else ""
    if first_word not in READ_ONLY_KEYWORDS:
        raise ToolError(
            f"run_sql_query only accepts SELECT/WITH statements, not {first_word!r}. "
            "This tool is deliberately scoped to read-only, even though "
            "sql_connection.execute_query() itself supports arbitrary SQL."
        )
    body_after_semicolon = stripped.split(";", 1)
    if len(body_after_semicolon) > 1 and body_after_semicolon[1].strip():
        raise ToolError(
            "run_sql_query does not accept multiple statements in one call."
        )
    return stripped


@mcp.resource("mssql://tables", mime_type="application/json")
def list_database_tables() -> list[dict]:
    """Always available as background context: the list of tables and
    views the connected SQL Server database exposes. The application
    attaches this automatically; the model does not need to request it."""
    conn = _get_connection()
    try:
        rows = sql_connection.execute_query(
            conn,
            "SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE "
            "FROM INFORMATION_SCHEMA.TABLES ORDER BY TABLE_SCHEMA, TABLE_NAME",
            user_id="mcp-server:list_database_tables",
        )
        return [
            {"schema": row[0], "table": row[1], "type": row[2]} for row in rows
        ]
    finally:
        conn.close()


@mcp.resource("mssql://tables/{table_name}", mime_type="application/json")
def describe_table(table_name: str) -> list[dict]:
    """Read-only column metadata for one specific table. Attach this when
    the current question is about a particular table's structure, so the
    model can see real column names/types instead of guessing them."""
    table_name = _validate_identifier(table_name)
    conn = _get_connection()
    try:
        rows = sql_connection.execute_query(
            conn,
            "SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE "
            "FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = "
            f"'{table_name}' ORDER BY ORDINAL_POSITION",
            user_id=f"mcp-server:describe_table:{table_name}",
        )
        if not rows:
            raise ResourceError(f"No table named {table_name!r} was found.")
        return [
            {"column": row[0], "data_type": row[1], "nullable": row[2] == "YES"}
            for row in rows
        ]
    finally:
        conn.close()


class QueryResult(BaseModel):
    columns: list[str]
    rows: list[dict]
    row_count: int
    message: str | None = None


@mcp.tool()
def run_sql_query(
    query: Annotated[str, Field(min_length=1, max_length=4000)],
    user_id: Annotated[str, Field(min_length=1, max_length=200)],
    max_rows: Annotated[int, Field(ge=1, le=1000)] = 100,
) -> QueryResult:
    """Call this whenever you need real data from the connected SQL Server
    database to answer a user's question - do not guess or make up
    numbers. Only read-only SELECT/WITH statements are accepted; anything
    else (INSERT/UPDATE/DELETE/DDL) is rejected before it touches the
    database. Always pass the real end user's identifier as user_id -
    every call is logged with it for audit (REQ-011). Results come back
    as named columns, not raw arrays, so you can reference each value by
    its column name. Capped at max_rows rows. If the query runs
    successfully but matches nothing, you get an empty rows list with a
    message explaining that - that's a normal, expected outcome, not a
    failure."""
    validated_query = _validate_read_only(query)
    conn = _get_connection()
    try:
        columns, raw_rows = sql_connection.execute_query(
            conn, validated_query, user_id, with_columns=True
        )
        limited_rows = raw_rows[:max_rows]
        named_rows = [dict(zip(columns, row)) for row in limited_rows]
        if not named_rows:
            return QueryResult(
                columns=columns,
                rows=[],
                row_count=0,
                message="Query executed successfully but returned no rows.",
            )
        return QueryResult(columns=columns, rows=named_rows, row_count=len(named_rows))
    finally:
        conn.close()


# Prompts can also return a list of typed Message objects (UserMessage/
# AssistantMessage) instead of a plain string, for multi-turn workflows
# that need to seed more than one conversation turn. Not needed here -
# this is a single instruction handed to the model in one turn - but the
# option exists.
@mcp.prompt()
def profile_table(table_name: str) -> str:
    """Use when a Data Engineer asks by name to profile a specific table
    (STORY-014): structure plus basic data-quality signals, not just a
    question answered from the data."""
    return (
        f"Profile the table `{table_name}`. Steps:\n"
        f"1. Read the `mssql://tables/{table_name}` resource for its columns. "
        "If that read fails because no table by this name exists, tell the "
        "user the table wasn't found and stop - do not guess at columns.\n"
        "2. Call run_sql_query with `SELECT COUNT(*) AS row_count "
        f"FROM {table_name}` to get the total row count. If row_count is 0, "
        "report the table as empty and skip steps 3-4 - do not report null "
        "or distinct counts for a table with no rows.\n"
        "3. For each column, call run_sql_query with "
        "`SELECT COUNT(*) - COUNT(<column>) AS null_count, "
        "COUNT(DISTINCT <column>) AS distinct_count FROM "
        f"{table_name}` to get null and distinct counts.\n"
        "4. Summarize: row count, and per column - data type, nullable, "
        "null count, distinct count."
    )


class BreakdownItem(BaseModel):
    label: Annotated[str, Field(min_length=1, max_length=200)]
    value: int | float


class ReportResults(BaseModel):
    metric: Annotated[str, Field(min_length=1, max_length=200)]
    aggregation: Literal["average", "sum", "count"]
    value: int | float
    breakdown: Annotated[list[BreakdownItem] | None, Field(default=None, max_length=1000)]


class GeneratedReport(BaseModel):
    report_format: Literal["pdf", "text"]
    content_base64: str
    byte_size: int


@mcp.resource("report://formats", mime_type="application/json")
def list_report_formats() -> list[str]:
    """Always available as background context: the report formats
    generate_report actually supports. Attach automatically so the model
    never has to guess a format value."""
    return sorted(report_generator._FORMAT_BUILDERS)


@mcp.tool()
def generate_report(
    report_format: Literal["pdf", "text"],
    results: ReportResults,
    user_id: Annotated[str, Field(min_length=1, max_length=200)],
) -> GeneratedReport:
    """Call this once you have an analytical result to hand the user as a
    downloadable report (REQ-007/REQ-018) rather than just a chat reply.
    Build `results` yourself from data you already gathered (e.g. via
    run_sql_query): metric is what was measured, aggregation is how
    (average/sum/count), value is the aggregate number, and breakdown is
    an optional list of {label, value} for the top contributing rows.
    There is no file-path argument - this always returns the report's
    bytes (base64-encoded) rather than writing to the server's disk."""
    try:
        report_bytes = report_generator.generate_report(
            report_format, results.model_dump(exclude_none=True), user_id
        )
    except REPORT_ERRORS as e:
        # report_generator/explanation_generator's own exceptions are plain
        # Exception subclasses, not ToolError - left uncaught, the SDK
        # deliberately drops their message text before it reaches the model
        # (mcp/server/mcpserver/tools/base.py: "a crash: the exception's own
        # text stays on the server"). Re-raising as ToolError is what
        # actually lets the model see *why* the call failed.
        raise ToolError(str(e)) from e
    return GeneratedReport(
        report_format=report_format,
        content_base64=base64.b64encode(report_bytes).decode("ascii"),
        byte_size=len(report_bytes),
    )


@mcp.prompt()
def create_report_from_query(query: str, report_format: str = "pdf") -> str:
    """Use when a user asks by name for a report/download answering a
    specific question (REQ-007/REQ-018), not just an in-chat answer."""
    return (
        f"Generate a {report_format} report answering: {query}\n"
        "Steps:\n"
        "1. Call run_sql_query with a SELECT that answers the question above.\n"
        "2. From the returned rows, build a results object: metric (what "
        "you measured), aggregation (one of average/sum/count), value "
        "(the aggregate number), and optionally breakdown (a list of "
        "{label, value} for the top contributing rows).\n"
        f'3. Call generate_report with report_format="{report_format}" '
        "and that results object.\n"
        "4. Tell the user the report was generated and its size."
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
