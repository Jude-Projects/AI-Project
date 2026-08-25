import csv
import json
import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

MAX_FILE_SIZE_BYTES = 80 * 1024 * 1024  # 80MB


class CsvFormatError(Exception):
    pass


class CsvMissingHeadersError(Exception):
    pass


class CsvTooLargeError(Exception):
    pass


def _is_int(value: str) -> bool:
    try:
        int(value)
        return True
    except ValueError:
        return False


def _is_float(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


def _infer_dtype(values: list) -> str:
    non_null = [v for v in values if v != ""]
    if not non_null:
        return "unknown"
    if all(_is_int(v) for v in non_null):
        return "int"
    if all(_is_float(v) for v in non_null):
        return "float"
    return "string"


def _count_nulls(values: list) -> int:
    return sum(1 for v in values if v == "")


def _find_duplicates(rows: list) -> list:
    counts: dict = {}
    order = []
    for row in rows:
        key = tuple(row.items())
        if key not in counts:
            order.append(key)
        counts[key] = counts.get(key, 0) + 1
    return [dict(key) for key in order if counts[key] > 1]


def analyze_csv(file_path: str, user_id: str) -> dict:
    file_size = os.path.getsize(file_path)
    logger.info(
        json.dumps(
            {
                "event": "csv_upload",
                "user_id": user_id,
                "file_name": os.path.basename(file_path),
                "file_size_bytes": file_size,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    )

    if file_size > MAX_FILE_SIZE_BYTES:
        raise CsvTooLargeError(
            f"File is {file_size} bytes, which exceeds the "
            f"{MAX_FILE_SIZE_BYTES}-byte upload limit."
        )

    try:
        with open(file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            rows = list(reader)
    except (csv.Error, UnicodeDecodeError) as e:
        raise CsvFormatError(f"Could not parse '{file_path}' as CSV: {e}") from e

    if not fieldnames:
        raise CsvMissingHeadersError(
            f"'{file_path}' has no header row to detect columns from."
        )

    columns = [
        {"name": name, "dtype": _infer_dtype([row.get(name, "") for row in rows])}
        for name in fieldnames
    ]
    duplicates = _find_duplicates(rows)
    null_counts = {
        name: _count_nulls([row.get(name, "") for row in rows]) for name in fieldnames
    }

    return {"columns": columns, "duplicates": duplicates, "null_counts": null_counts}
