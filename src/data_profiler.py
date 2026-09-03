import json
import logging
import time
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

PROFILING_TIMEOUT_SECONDS = 10


class ProfilingTimeoutError(Exception):
    pass


class DataQualityMetricError(Exception):
    pass


def _column_names(data: list) -> list:
    names = []
    for row in data:
        for key in row:
            if key not in names:
                names.append(key)
    return names


def _infer_dtype(values: list) -> str:
    non_null = [v for v in values if v is not None]
    if not non_null:
        return "unknown"
    if all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in non_null):
        return "numeric"
    return "string"


def _profile_column(name: str, data: list) -> dict:
    values = [row.get(name) for row in data]
    non_null = [v for v in values if v is not None]
    dtype = _infer_dtype(values)

    profile = {
        "name": name,
        "dtype": dtype,
        "null_count": len(values) - len(non_null),
        "distinct_count": len(set(non_null)),
    }

    if dtype == "numeric" and non_null:
        profile["min"] = min(non_null)
        profile["max"] = max(non_null)
        profile["mean"] = sum(non_null) / len(non_null)

    return profile


def _count_duplicates(data: list) -> int:
    seen = set()
    duplicate_count = 0
    for row in data:
        key = tuple(sorted(row.items()))
        if key in seen:
            duplicate_count += 1
        else:
            seen.add(key)
    return duplicate_count


def profile_data(data: list, user_id: str) -> dict:
    logger.info(
        json.dumps(
            {
                "event": "data_profiled",
                "user_id": user_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    )

    started_at = time.monotonic()
    try:
        columns = [_profile_column(name, data) for name in _column_names(data)]
        duplicate_count = _count_duplicates(data)
    except TypeError as e:
        raise DataQualityMetricError(
            f"Could not compute a data quality metric: {e}"
        ) from e
    elapsed_seconds = time.monotonic() - started_at

    if elapsed_seconds > PROFILING_TIMEOUT_SECONDS:
        raise ProfilingTimeoutError(
            f"Profiling took {elapsed_seconds:.1f}s, which exceeds the "
            f"{PROFILING_TIMEOUT_SECONDS}s limit."
        )

    return {
        "row_count": len(data),
        "columns": columns,
        "duplicate_count": duplicate_count,
    }
