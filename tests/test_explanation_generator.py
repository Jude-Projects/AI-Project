import json
import logging
from datetime import datetime

import pytest

from explanation_generator import (
    ComplexityOverloadError,
    LanguageBarrierError,
    MisinterpretationError,
    explain_results,
)


def test_explain_results_summarizes_average():
    results = {"metric": "revenue", "aggregation": "average", "value": 45231.5}

    summary = explain_results(results, user_id="user-123")

    assert summary == "The average revenue is 45,231.50."


def test_explain_results_summarizes_sum():
    results = {"metric": "sales", "aggregation": "sum", "value": 120000}

    summary = explain_results(results, user_id="user-123")

    assert summary == "The total sales is 120,000."


def test_explain_results_summarizes_count():
    results = {"metric": "orders", "aggregation": "count", "value": 42}

    summary = explain_results(results, user_id="user-123")

    assert summary == "There are 42 orders."


def test_explain_results_simplifies_large_breakdown_to_top_contributors():
    results = {
        "metric": "revenue",
        "aggregation": "average",
        "value": 45231.5,
        "breakdown": [
            {"label": "West", "value": 50000},
            {"label": "East", "value": 40000},
            {"label": "South", "value": 30000},
            {"label": "North", "value": 20000},
            {"label": "Central", "value": 10000},
        ],
    }

    summary = explain_results(results, user_id="user-123")

    assert summary == (
        "The average revenue is 45,231.50. The top contributors are "
        "West (50,000), East (40,000), and South (30,000), "
        "with 2 more categories not shown."
    )


def test_explain_results_shows_all_items_when_breakdown_is_small():
    results = {
        "metric": "revenue",
        "aggregation": "sum",
        "value": 90000,
        "breakdown": [
            {"label": "West", "value": 50000},
            {"label": "East", "value": 40000},
        ],
    }

    summary = explain_results(results, user_id="user-123")

    assert summary == (
        "The total revenue is 90,000. The top contributors are "
        "West (50,000) and East (40,000)."
    )


def test_explain_results_raises_on_unrecognized_aggregation():
    results = {"metric": "revenue", "aggregation": "median", "value": 100}

    with pytest.raises(MisinterpretationError):
        explain_results(results, user_id="user-123")


def test_explain_results_raises_on_missing_required_key():
    results = {"metric": "revenue", "aggregation": "average"}  # no "value"

    with pytest.raises(MisinterpretationError):
        explain_results(results, user_id="user-123")


def test_explain_results_raises_on_complexity_overload():
    results = {
        "metric": "revenue",
        "aggregation": "sum",
        "value": 1000000,
        "breakdown": [{"label": f"region-{i}", "value": i} for i in range(1001)],
    }

    with pytest.raises(ComplexityOverloadError):
        explain_results(results, user_id="user-123")


def test_explain_results_raises_on_non_ascii_metric():
    results = {"metric": "ingrésos", "aggregation": "average", "value": 100}

    with pytest.raises(LanguageBarrierError):
        explain_results(results, user_id="user-123")


def test_explain_results_raises_on_non_ascii_breakdown_label():
    results = {
        "metric": "revenue",
        "aggregation": "sum",
        "value": 100,
        "breakdown": [{"label": "México", "value": 50}],
    }

    with pytest.raises(LanguageBarrierError):
        explain_results(results, user_id="user-123")


def test_explain_results_logs_request_with_user_metric_and_aggregation(caplog):
    results = {"metric": "revenue", "aggregation": "average", "value": 100}

    with caplog.at_level(logging.INFO, logger="explanation_generator"):
        explain_results(results, user_id="user-123")

    assert len(caplog.records) == 1
    logged = json.loads(caplog.records[0].message)
    assert logged["event"] == "explanation_requested"
    assert logged["user_id"] == "user-123"
    assert logged["metric"] == "revenue"
    assert logged["aggregation"] == "average"
    # Fails loudly if "timestamp" is missing or not a real ISO-8601 datetime,
    # rather than silently accepting any string in that field.
    datetime.fromisoformat(logged["timestamp"])
