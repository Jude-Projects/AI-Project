import json
import logging
from datetime import datetime, timezone

import pyodbc

from sql_connection import connect, execute_query

logger = logging.getLogger(__name__)


class SchemaAccessError(Exception):
    pass

_TABLES_QUERY = (
    "SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE "
    "FROM INFORMATION_SCHEMA.TABLES ORDER BY TABLE_SCHEMA, TABLE_NAME"
)

_COLUMNS_QUERY = (
    "SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE "
    "FROM INFORMATION_SCHEMA.COLUMNS ORDER BY TABLE_NAME, ORDINAL_POSITION"
)

_RELATIONSHIPS_QUERY = (
    "SELECT fk.TABLE_NAME AS from_table, kcu.COLUMN_NAME AS from_column, "
    "       pk.TABLE_NAME AS to_table, pkcu.COLUMN_NAME AS to_column "
    "FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc "
    "JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS fk "
    "  ON rc.CONSTRAINT_NAME = fk.CONSTRAINT_NAME "
    "JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS pk "
    "  ON rc.UNIQUE_CONSTRAINT_NAME = pk.CONSTRAINT_NAME "
    "JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu "
    "  ON kcu.CONSTRAINT_NAME = fk.CONSTRAINT_NAME "
    "JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE pkcu "
    "  ON pkcu.CONSTRAINT_NAME = pk.CONSTRAINT_NAME"
)


def inspect_schema(connection_string: str, user_id: str) -> dict:
    logger.info(
        json.dumps(
            {
                "event": "schema_inspected",
                "user_id": user_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    )

    try:
        conn = connect(connection_string)

        tables_rows = execute_query(conn, _TABLES_QUERY, user_id)
        tables = [
            {"schema": row[0], "name": row[1], "type": row[2], "columns": []}
            for row in tables_rows
        ]
        tables_by_name = {table["name"]: table for table in tables}

        columns_rows = execute_query(conn, _COLUMNS_QUERY, user_id)
        for table_name, column_name, data_type in columns_rows:
            if table_name in tables_by_name:
                tables_by_name[table_name]["columns"].append(
                    {"name": column_name, "data_type": data_type}
                )

        relationships_rows = execute_query(conn, _RELATIONSHIPS_QUERY, user_id)
        relationships = [
            {
                "from_table": row[0],
                "from_column": row[1],
                "to_table": row[2],
                "to_column": row[3],
            }
            for row in relationships_rows
        ]
    except (pyodbc.Error, ValueError) as e:
        raise SchemaAccessError(f"Could not inspect the schema: {e}") from e

    return {"tables": tables, "relationships": relationships}
