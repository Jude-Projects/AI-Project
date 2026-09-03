import json
import logging
from datetime import datetime, timezone

import pyodbc

logger = logging.getLogger(__name__)


class CertificateError(Exception):
    pass


class ProtocolMismatchError(Exception):
    pass


class EncryptionFailureError(Exception):
    pass


def _classify_connection_error(error: pyodbc.Error) -> Exception:
    message = str(error).lower()
    if "certificate" in message:
        return CertificateError(str(error))
    if "protocol" in message or "tls version" in message:
        return ProtocolMismatchError(str(error))
    if "ssl" in message or "tls" in message or "encrypt" in message:
        return EncryptionFailureError(str(error))
    return error


def _is_encrypted(connection_string: str) -> bool:
    attributes = {}
    for pair in connection_string.split(";"):
        key, sep, value = pair.partition("=")
        if sep:
            attributes[key.strip().lower()] = value.strip().lower()
    return attributes.get("encrypt") == "yes"


def connect(connection_string: str, user_id: str = None) -> pyodbc.Connection:
    encrypted = _is_encrypted(connection_string)

    # Logged before the encryption check, not after - a blocked, unencrypted
    # attempt belongs in the audit trail too, arguably more so than a
    # successful one.
    logger.info(
        json.dumps(
            {
                "event": "connection_configured",
                "user_id": user_id,
                "encrypted": encrypted,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    )

    if not encrypted:
        raise ValueError(
            "Refusing to connect: connection string must set Encrypt=yes "
            "(REQ-015 requires encrypted SQL Server connections)."
        )

    try:
        return pyodbc.connect(connection_string)
    except pyodbc.Error as e:
        classified = _classify_connection_error(e)
        if classified is e:
            raise  # no pattern matched - re-raise the original error as-is
        raise classified from e


def execute_query(
    conn: pyodbc.Connection, query: str, user_id: str, with_columns: bool = False
) -> list | tuple[list[str], list]:
    logger.info(
        json.dumps(
            {
                "event": "query_execution",
                "user_id": user_id,
                "query": query,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    )
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    if with_columns:
        columns = [col[0] for col in cursor.description] if cursor.description else []
        return columns, rows
    return rows
