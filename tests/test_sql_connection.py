import json
import logging
from datetime import datetime
from unittest.mock import MagicMock, patch

import pyodbc
import pytest

from sql_connection import (
    CertificateError,
    EncryptionFailureError,
    ProtocolMismatchError,
    connect,
    execute_query,
)


def test_connect_calls_pyodbc_connect_with_connection_string():
    with patch("sql_connection.pyodbc.connect") as mock_connect:
        mock_connect.return_value = MagicMock()
        connection_string = (
            "DRIVER={ODBC Driver 18 for SQL Server};SERVER=test;DATABASE=test;"
            "UID=user;PWD=pass;Encrypt=yes"
        )

        result = connect(connection_string)

        mock_connect.assert_called_once_with(connection_string)
        assert result is mock_connect.return_value


def test_connect_raises_error_with_message_on_invalid_connection_string():
    with patch("sql_connection.pyodbc.connect") as mock_connect:
        mock_connect.side_effect = pyodbc.Error(
            "HY000", "Invalid connection string attribute"
        )
        # Well-formed enough to pass the local encryption check, so this
        # exercises pyodbc's own rejection rather than our encryption gate.
        invalid_connection_string = "SERVER=does-not-exist;Encrypt=yes"

        with pytest.raises(pyodbc.Error) as exc_info:
            connect(invalid_connection_string)

        assert "Invalid connection string attribute" in str(exc_info.value)


def test_connect_rejects_connection_string_without_encryption():
    with patch("sql_connection.pyodbc.connect") as mock_connect:
        unencrypted_connection_string = (
            "DRIVER={ODBC Driver 18 for SQL Server};SERVER=test;DATABASE=test;"
            "UID=user;PWD=pass"
        )

        with pytest.raises(ValueError, match="REQ-015"):
            connect(unencrypted_connection_string)

        mock_connect.assert_not_called()


def test_connect_rejects_connection_string_with_encrypt_explicitly_no():
    with patch("sql_connection.pyodbc.connect") as mock_connect:
        with pytest.raises(ValueError, match="REQ-015"):
            connect("SERVER=test;Encrypt=no")

        mock_connect.assert_not_called()


def test_connect_accepts_encrypt_case_insensitively():
    with patch("sql_connection.pyodbc.connect") as mock_connect:
        mock_connect.return_value = MagicMock()

        connect("SERVER=test;ENCRYPT=YES")

        mock_connect.assert_called_once()


def test_connect_raises_certificate_error_on_untrusted_certificate():
    with patch("sql_connection.pyodbc.connect") as mock_connect:
        mock_connect.side_effect = pyodbc.Error(
            "08001",
            "[08001] SSL Provider: The certificate chain was issued by an "
            "authority that is not trusted.",
        )

        with pytest.raises(CertificateError):
            connect("SERVER=test;Encrypt=yes")


def test_connect_raises_protocol_mismatch_error_on_protocol_version_mismatch():
    with patch("sql_connection.pyodbc.connect") as mock_connect:
        mock_connect.side_effect = pyodbc.Error(
            "08001",
            "[08001] SSL Provider: The client and server cannot communicate "
            "because they do not possess a common SSL protocol version.",
        )

        with pytest.raises(ProtocolMismatchError):
            connect("SERVER=test;Encrypt=yes")


def test_connect_raises_encryption_failure_error_on_other_ssl_failure():
    with patch("sql_connection.pyodbc.connect") as mock_connect:
        mock_connect.side_effect = pyodbc.Error(
            "08001",
            "[08001] SSL Provider: A fatal error occurred while attempting "
            "to encrypt the incoming connection.",
        )

        with pytest.raises(EncryptionFailureError):
            connect("SERVER=test;Encrypt=yes")


def test_connect_logs_connection_configuration_with_user_id(caplog):
    with patch("sql_connection.pyodbc.connect") as mock_connect:
        mock_connect.return_value = MagicMock()

        with caplog.at_level(logging.INFO, logger="sql_connection"):
            connect("SERVER=test;Encrypt=yes", user_id="user-123")

    assert len(caplog.records) == 1
    logged = json.loads(caplog.records[0].message)
    assert logged["event"] == "connection_configured"
    assert logged["user_id"] == "user-123"
    assert logged["encrypted"] is True
    # Fails loudly if "timestamp" is missing or not a real ISO-8601 datetime,
    # rather than silently accepting any string in that field.
    datetime.fromisoformat(logged["timestamp"])


def test_connect_logs_blocked_unencrypted_attempt_before_raising(caplog):
    with caplog.at_level(logging.INFO, logger="sql_connection"):
        with pytest.raises(ValueError, match="REQ-015"):
            connect("SERVER=test;Encrypt=no", user_id="user-123")

    assert len(caplog.records) == 1
    logged = json.loads(caplog.records[0].message)
    assert logged["event"] == "connection_configured"
    assert logged["user_id"] == "user-123"
    assert logged["encrypted"] is False


def test_execute_query_runs_query_and_returns_rows():
    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.fetchall.return_value = [(1, "a"), (2, "b")]
    query = "SELECT id, name FROM widgets"

    result = execute_query(mock_conn, query, user_id="user-123")

    mock_conn.cursor.assert_called_once_with()
    mock_cursor.execute.assert_called_once_with(query)
    mock_cursor.fetchall.assert_called_once_with()
    assert result == [(1, "a"), (2, "b")]


def test_execute_query_with_columns_returns_column_names_and_rows():
    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.fetchall.return_value = [(1, "a"), (2, "b")]
    mock_cursor.description = [("id", None), ("name", None)]

    columns, rows = execute_query(
        mock_conn, "SELECT id, name FROM widgets", user_id="user-123", with_columns=True
    )

    assert columns == ["id", "name"]
    assert rows == [(1, "a"), (2, "b")]


def test_execute_query_with_columns_handles_no_description():
    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.fetchall.return_value = []
    mock_cursor.description = None

    columns, rows = execute_query(
        mock_conn, "SELECT 1 WHERE 1=0", user_id="user-123", with_columns=True
    )

    assert columns == []
    assert rows == []


def test_execute_query_raises_error_on_sql_syntax_error():
    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.execute.side_effect = pyodbc.ProgrammingError(
        "42000", "Incorrect syntax near 'FORM'"
    )
    bad_query = "SELECT id FORM widgets"

    with pytest.raises(pyodbc.ProgrammingError) as exc_info:
        execute_query(mock_conn, bad_query, user_id="user-123")

    assert "Incorrect syntax" in str(exc_info.value)


def test_execute_query_logs_user_id_and_timestamp(caplog):
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.fetchall.return_value = []
    query = "SELECT 1"

    with caplog.at_level(logging.INFO, logger="sql_connection"):
        execute_query(mock_conn, query, user_id="user-123")

    assert len(caplog.records) == 1
    logged = json.loads(caplog.records[0].message)
    assert logged["event"] == "query_execution"
    assert logged["user_id"] == "user-123"
    assert logged["query"] == query
    # Fails loudly if "timestamp" is missing or not a real ISO-8601 datetime,
    # rather than silently accepting any string in that field.
    datetime.fromisoformat(logged["timestamp"])
