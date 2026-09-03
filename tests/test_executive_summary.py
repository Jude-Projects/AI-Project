import json
import logging
import time
from datetime import datetime
from unittest.mock import patch

import pytest

from executive_summary import SummaryGenerationTimeoutError, generate_executive_summary

_KPIS = [
    {
        "name": "Total Revenue",
        "metric": "revenue",
        "aggregation": "sum",
        "data": [{"revenue": 100}, {"revenue": 200}],
    },
    {
        "name": "Average Order Value",
        "metric": "order_value",
        "aggregation": "average",
        "data": [{"order_value": 50}, {"order_value": 150}],
    },
    {
        "name": "Order Count",
        "metric": "order_value",
        "aggregation": "count",
        "data": [{"order_value": 50}, {"order_value": 150}],
    },
]


def test_generate_executive_summary_computes_all_kpis():
    result = generate_executive_summary(_KPIS, user_id="user-123")

    assert result["summary"] == "Generated 3 of 3 KPIs successfully."
    assert result["kpis"]["Total Revenue"] == {
        "status": "ok",
        "answer": 300,
        "explanation": "The total revenue is 300.",
    }
    assert result["kpis"]["Average Order Value"]["status"] == "ok"
    assert result["kpis"]["Average Order Value"]["answer"] == 100.0
    assert result["kpis"]["Order Count"] == {
        "status": "ok",
        "answer": 2,
        "explanation": "There are 2 order_value.",
    }


def test_generate_executive_summary_indicates_missing_data_and_returns_available_kpis():
    kpis = _KPIS + [
        {"name": "Refund Rate", "metric": "refund_amount", "aggregation": "sum", "data": []}
    ]

    result = generate_executive_summary(kpis, user_id="user-123")

    assert result["summary"] == "Generated 3 of 4 KPIs successfully; 1 could not be computed."
    assert result["kpis"]["Refund Rate"] == {
        "status": "missing_data",
        "message": "No data was provided for 'Refund Rate'.",
    }
    assert result["kpis"]["Total Revenue"]["status"] == "ok"


def test_generate_executive_summary_marks_calculation_error_without_failing_others():
    kpis = _KPIS + [
        {
            "name": "Broken KPI",
            "metric": "revenue",
            "aggregation": "average",
            "data": [{"revenue": "not-a-number"}],
        }
    ]

    result = generate_executive_summary(kpis, user_id="user-123")

    assert result["summary"] == "Generated 3 of 4 KPIs successfully; 1 could not be computed."
    assert result["kpis"]["Broken KPI"]["status"] == "calculation_error"
    assert result["kpis"]["Total Revenue"]["status"] == "ok"


def test_generate_executive_summary_raises_on_timeout():
    def _slow_analyze(*args, **kwargs):
        time.sleep(0.2)
        return {"answer": 300, "explanation": "The total revenue is 300."}

    with patch("executive_summary.analyze_data", side_effect=_slow_analyze):
        with patch("executive_summary.SUMMARY_TIMEOUT_SECONDS", 0.02):
            with pytest.raises(SummaryGenerationTimeoutError):
                generate_executive_summary(_KPIS, user_id="user-123")


def test_generate_executive_summary_logs_request_with_user_and_timestamp(caplog):
    with caplog.at_level(logging.INFO, logger="executive_summary"):
        generate_executive_summary(_KPIS, user_id="user-123")

    assert len(caplog.records) == 1
    logged = json.loads(caplog.records[0].message)
    assert logged["event"] == "executive_summary_requested"
    assert logged["user_id"] == "user-123"
    # Fails loudly if "timestamp" is missing or not a real ISO-8601 datetime,
    # rather than silently accepting any string in that field.
    datetime.fromisoformat(logged["timestamp"])
