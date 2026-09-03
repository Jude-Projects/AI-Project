import json
import logging
from datetime import datetime

import pytest

from alert_engine import RecommendationError, generate_alerts, generate_recommendation

_LOW_REVENUE_RULE = {
    "name": "Low Revenue Alert",
    "metric": "revenue",
    "aggregation": "average",
    "data": [{"revenue": 50}, {"revenue": 60}, {"revenue": 55}],
    "threshold": 100,
    "condition": "below",
}

_HIGH_REVENUE_RULE = {
    "name": "High Revenue Alert",
    "metric": "revenue",
    "aggregation": "average",
    "data": [{"revenue": 500}, {"revenue": 600}, {"revenue": 550}],
    "threshold": 1000,
    "condition": "above",
}


def test_generate_alerts_notifies_on_important_change():
    result = generate_alerts([_LOW_REVENUE_RULE], user_id="user-123")

    assert result == [
        {
            "name": "Low Revenue Alert",
            "metric": "revenue",
            "condition": "below",
            "status": "triggered",
            "value": 55.0,
            "threshold": 100,
            "message": (
                "'Low Revenue Alert' triggered: revenue is 55.0, which is "
                "below the threshold of 100."
            ),
        }
    ]


def test_generate_alerts_does_not_trigger_when_condition_not_met():
    result = generate_alerts([_HIGH_REVENUE_RULE], user_id="user-123")

    assert result == [
        {
            "name": "High Revenue Alert",
            "metric": "revenue",
            "condition": "above",
            "status": "not_triggered",
            "value": 550.0,
            "threshold": 1000,
        }
    ]


def test_generate_recommendation_provides_actionable_advice():
    alerts = generate_alerts([_LOW_REVENUE_RULE], user_id="user-123")

    recommendation = generate_recommendation(alerts[0], user_id="user-123")

    assert recommendation == (
        "Recommended action: review recent activity related to "
        "'Low Revenue Alert', since revenue (55.0) is below the threshold of 100."
    )


def test_generate_alerts_flags_insufficient_data_to_avoid_false_positive():
    sparse_rule = {
        "name": "Sparse Rule",
        "metric": "revenue",
        "aggregation": "average",
        "data": [{"revenue": 10}],  # below MIN_SAMPLE_SIZE
        "threshold": 100,
        "condition": "below",
    }

    result = generate_alerts([sparse_rule], user_id="user-123")

    assert result == [
        {
            "name": "Sparse Rule",
            "status": "insufficient_data",
            "message": (
                "'Sparse Rule' has only 1 data point(s); at least 3 are "
                "required to evaluate reliably."
            ),
        }
    ]


def test_generate_alerts_marks_broken_rule_without_missing_other_alerts():
    broken_rule = {
        "name": "Broken Rule",
        "metric": "revenue",
        "aggregation": "average",
        "data": [{"revenue": "not-a-number"}, {"revenue": 1}, {"revenue": 2}],
        "threshold": 100,
        "condition": "below",
    }

    result = generate_alerts([broken_rule, _LOW_REVENUE_RULE], user_id="user-123")

    assert result[0]["status"] == "evaluation_error"
    assert result[1]["status"] == "triggered"  # the other rule still evaluates fine


def test_generate_recommendation_raises_for_non_triggered_alert():
    alert = {
        "name": "High Revenue Alert",
        "metric": "revenue",
        "condition": "above",
        "status": "not_triggered",
        "value": 550.0,
        "threshold": 1000,
    }

    with pytest.raises(RecommendationError):
        generate_recommendation(alert, user_id="user-123")


def test_generate_recommendation_raises_for_missing_required_fields():
    with pytest.raises(RecommendationError):
        generate_recommendation({"status": "triggered"}, user_id="user-123")


def test_generate_alerts_logs_request_with_user_and_timestamp(caplog):
    with caplog.at_level(logging.INFO, logger="alert_engine"):
        generate_alerts([_LOW_REVENUE_RULE], user_id="user-123")

    assert len(caplog.records) == 1
    logged = json.loads(caplog.records[0].message)
    assert logged["event"] == "alerts_requested"
    assert logged["user_id"] == "user-123"
    # Fails loudly if "timestamp" is missing or not a real ISO-8601 datetime,
    # rather than silently accepting any string in that field.
    datetime.fromisoformat(logged["timestamp"])
