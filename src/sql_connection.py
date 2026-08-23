import json
import logging
from datetime import datetime, timezone

import pyodbc

logger = logging.getLogger(__name__)


def _is_encrypted(connection_string: str) -> bool:
    attributes = {}
    for pair in connection_string.split(";"):
        key, sep, value = pair.partition("=")
        if sep:
            attributes[key.strip().lower()] = value.strip().lower()
    return attributes.get("encrypt") == "yes"


def connect(connection_string: str) -> pyodbc.Connection:
    if not _is_encrypted(connection_string):
        raise ValueError(
            "Refusing to connect: connection string must set Encrypt=yes "
            "(REQ-015 requires encrypted SQL Server connections)."
        )
    return pyodbc.connect(connection_string)


def execute_query(conn: pyodbc.Connection, query: str, user_id: str) -> list:
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
    return cursor.fetchall()
