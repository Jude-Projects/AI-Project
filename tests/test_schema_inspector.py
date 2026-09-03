import json
import logging
from datetime import datetime
from unittest.mock import MagicMock, patch

import pyodbc
import pytest

from schema_inspector import SchemaAccessError, inspect_schema


def test_inspect_schema_assembles_tables_columns_and_relationships():
    tables_rows = [("dbo", "Orders", "BASE TABLE"), ("dbo", "Customers", "BASE TABLE")]
    columns_rows = [
        ("Orders", "OrderID", "int"),
        ("Orders", "CustomerID", "int"),
        ("Customers", "CustomerID", "int"),
    ]
    relationships_rows = [("Orders", "CustomerID", "Customers", "CustomerID")]

    with patch("schema_inspector.connect") as mock_connect:
        mock_connect.return_value = MagicMock()
        with patch(
            "schema_inspector.execute_query",
            side_effect=[tables_rows, columns_rows, relationships_rows],
        ):
            result = inspect_schema(
                "DRIVER={ODBC Driver 18 for SQL Server};SERVER=test;Encrypt=yes",
                user_id="user-123",
            )

    assert result["tables"] == [
        {
            "schema": "dbo",
            "name": "Orders",
            "type": "BASE TABLE",
            "columns": [
                {"name": "OrderID", "data_type": "int"},
                {"name": "CustomerID", "data_type": "int"},
            ],
        },
        {
            "schema": "dbo",
            "name": "Customers",
            "type": "BASE TABLE",
            "columns": [{"name": "CustomerID", "data_type": "int"}],
        },
    ]
    assert result["relationships"] == [
        {
            "from_table": "Orders",
            "from_column": "CustomerID",
            "to_table": "Customers",
            "to_column": "CustomerID",
        }
    ]


def test_inspect_schema_raises_on_connection_failure():
    with patch("schema_inspector.connect") as mock_connect:
        mock_connect.side_effect = pyodbc.Error("HY000", "Connection failed")

        with pytest.raises(SchemaAccessError):
            inspect_schema(
                "DRIVER={ODBC Driver 18 for SQL Server};SERVER=test;Encrypt=yes",
                user_id="user-123",
            )


def test_inspect_schema_raises_on_query_failure():
    with patch("schema_inspector.connect") as mock_connect:
        mock_connect.return_value = MagicMock()
        with patch(
            "schema_inspector.execute_query",
            side_effect=pyodbc.ProgrammingError("42000", "Incorrect syntax"),
        ):
            with pytest.raises(SchemaAccessError):
                inspect_schema(
                    "DRIVER={ODBC Driver 18 for SQL Server};SERVER=test;Encrypt=yes",
                    user_id="user-123",
                )


def test_inspect_schema_logs_request_with_user_and_timestamp(caplog):
    with patch("schema_inspector.connect") as mock_connect:
        mock_connect.return_value = MagicMock()
        with patch("schema_inspector.execute_query", side_effect=[[], [], []]):
            with caplog.at_level(logging.INFO, logger="schema_inspector"):
                inspect_schema(
                    "DRIVER={ODBC Driver 18 for SQL Server};SERVER=test;Encrypt=yes",
                    user_id="user-123",
                )

    assert len(caplog.records) == 1
    logged = json.loads(caplog.records[0].message)
    assert logged["event"] == "schema_inspected"
    assert logged["user_id"] == "user-123"
    # Fails loudly if "timestamp" is missing or not a real ISO-8601 datetime,
    # rather than silently accepting any string in that field.
    datetime.fromisoformat(logged["timestamp"])
