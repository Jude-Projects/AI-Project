import json
import logging
import time
from datetime import datetime
from unittest.mock import patch

import pytest

from data_profiler import DataQualityMetricError, ProfilingTimeoutError, profile_data

_DATA = [
    {"region": "West", "revenue": 100},
    {"region": "East", "revenue": 200},
    {"region": "East", "revenue": 200},  # exact duplicate of the row above
    {"region": None, "revenue": 300},
]


def test_profile_data_computes_distribution_and_quality_metrics():
    result = profile_data(_DATA, user_id="user-123")

    assert result["row_count"] == 4
    assert result["duplicate_count"] == 1

    columns = {col["name"]: col for col in result["columns"]}
    assert columns["revenue"] == {
        "name": "revenue",
        "dtype": "numeric",
        "null_count": 0,
        "distinct_count": 3,
        "min": 100,
        "max": 300,
        "mean": 200.0,
    }
    assert columns["region"] == {
        "name": "region",
        "dtype": "string",
        "null_count": 1,
        "distinct_count": 2,
    }


def test_profile_data_raises_on_unhashable_value():
    data = [{"tags": ["a", "b"]}, {"tags": ["c"]}]  # lists aren't hashable

    with pytest.raises(DataQualityMetricError):
        profile_data(data, user_id="user-123")


def test_profile_data_raises_on_timeout():
    def _slow_profile_column(name, data):
        time.sleep(0.2)
        return {"name": name, "dtype": "numeric", "null_count": 0, "distinct_count": 1}

    with patch("data_profiler._profile_column", side_effect=_slow_profile_column):
        with patch("data_profiler.PROFILING_TIMEOUT_SECONDS", 0.02):
            with pytest.raises(ProfilingTimeoutError):
                profile_data(_DATA, user_id="user-123")


def test_profile_data_logs_request_with_user_and_timestamp(caplog):
    with caplog.at_level(logging.INFO, logger="data_profiler"):
        profile_data(_DATA, user_id="user-123")

    assert len(caplog.records) == 1
    logged = json.loads(caplog.records[0].message)
    assert logged["event"] == "data_profiled"
    assert logged["user_id"] == "user-123"
    # Fails loudly if "timestamp" is missing or not a real ISO-8601 datetime,
    # rather than silently accepting any string in that field.
    datetime.fromisoformat(logged["timestamp"])
