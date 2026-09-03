import json
import logging
import time
from datetime import datetime
from unittest.mock import patch

import pytest

from data_analyzer import (
    AnalysisTimeoutError,
    DataInconsistencyError,
    UnsupportedQueryTypeError,
    analyze_data,
)


def test_analyze_data_answers_average_question():
    data = [{"region": "West", "revenue": 100}, {"region": "East", "revenue": 200}]

    result = analyze_data(
        "What is the average revenue?", data, metric="revenue", user_id="user-123"
    )

    assert result["answer"] == 150
    assert result["explanation"] == "The average revenue is 150.00."


def test_analyze_data_answers_sum_question():
    data = [{"region": "West", "revenue": 100}, {"region": "East", "revenue": 200}]

    result = analyze_data(
        "What is the total revenue?", data, metric="revenue", user_id="user-123"
    )

    assert result["answer"] == 300
    assert result["explanation"] == "The total revenue is 300."


def test_analyze_data_answers_count_question():
    data = [{"region": "West", "revenue": 100}, {"region": "East", "revenue": 200}]

    result = analyze_data(
        "How many regions are there?", data, metric="revenue", user_id="user-123"
    )

    assert result["answer"] == 2
    assert result["explanation"] == "There are 2 revenue."


def test_analyze_data_provides_detailed_breakdown_for_complex_question():
    data = [
        {"region": "West", "revenue": 500},
        {"region": "East", "revenue": 400},
        {"region": "South", "revenue": 300},
        {"region": "North", "revenue": 200},
    ]

    result = analyze_data(
        "What is the total revenue?",
        data,
        metric="revenue",
        user_id="user-123",
        group_by="region",
    )

    assert result["answer"] == 1400
    assert result["explanation"] == (
        "The total revenue is 1,400. The top contributors are "
        "West (500), East (400), and South (300), with 1 more categories not shown."
    )


def test_analyze_data_raises_on_unsupported_query_type_for_comparison():
    data = [{"region": "West", "revenue": 100}]

    with pytest.raises(UnsupportedQueryTypeError):
        analyze_data(
            "Compare Q1 versus Q2 revenue.", data, metric="revenue", user_id="user-123"
        )


def test_analyze_data_raises_on_unsupported_query_type_for_unrecognized():
    data = [{"region": "West", "revenue": 100}]

    with pytest.raises(UnsupportedQueryTypeError):
        analyze_data(
            "What's the weather like today?", data, metric="revenue", user_id="user-123"
        )


def test_analyze_data_raises_on_empty_data():
    with pytest.raises(DataInconsistencyError):
        analyze_data(
            "What is the average revenue?", [], metric="revenue", user_id="user-123"
        )


def test_analyze_data_raises_on_missing_metric_field():
    data = [{"region": "West", "revenue": 100}, {"region": "East"}]

    with pytest.raises(DataInconsistencyError):
        analyze_data(
            "What is the average revenue?", data, metric="revenue", user_id="user-123"
        )


def test_analyze_data_raises_on_non_numeric_metric_value():
    data = [{"region": "West", "revenue": "not-a-number"}]

    with pytest.raises(DataInconsistencyError):
        analyze_data(
            "What is the average revenue?", data, metric="revenue", user_id="user-123"
        )


def test_analyze_data_raises_on_analysis_timeout():
    data = [{"region": "West", "revenue": 100}]

    def _slow_sum(values):
        time.sleep(0.2)
        return sum(values)

    with patch.dict(
        "data_analyzer._AGGREGATORS", {"average": lambda values: _slow_sum(values)}
    ):
        with patch("data_analyzer.ANALYSIS_TIMEOUT_SECONDS", 0.02):
            with pytest.raises(AnalysisTimeoutError):
                analyze_data(
                    "What is the average revenue?",
                    data,
                    metric="revenue",
                    user_id="user-123",
                )


def test_analyze_data_logs_question_answer_and_user(caplog):
    data = [{"region": "West", "revenue": 100}, {"region": "East", "revenue": 200}]

    with caplog.at_level(logging.INFO, logger="data_analyzer"):
        analyze_data(
            "What is the average revenue?", data, metric="revenue", user_id="user-123"
        )

    assert len(caplog.records) == 1
    logged = json.loads(caplog.records[0].message)
    assert logged["event"] == "analysis_answered"
    assert logged["user_id"] == "user-123"
    assert logged["question"] == "What is the average revenue?"
    assert logged["answer"] == 150
    # Fails loudly if "timestamp" is missing or not a real ISO-8601 datetime,
    # rather than silently accepting any string in that field.
    datetime.fromisoformat(logged["timestamp"])
