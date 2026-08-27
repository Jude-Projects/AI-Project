import json
import logging
import time
from datetime import datetime
from unittest.mock import patch

import pytest

from question_interpreter import (
    QuestionInterpretationTimeoutError,
    UnsupportedLanguageError,
    interpret_question,
)


def test_interpret_question_recognizes_average_intent():
    result = interpret_question(
        "What is the average revenue by region?", user_id="user-123"
    )

    assert result["status"] == "confident"
    assert result["interpretations"] == ["average"]


def test_interpret_question_recognizes_comparison_intent():
    result = interpret_question(
        "Compare sales in Q1 versus Q2.", user_id="user-123"
    )

    assert result["status"] == "confident"
    assert result["interpretations"] == ["comparison"]


def test_interpret_question_flags_ambiguous_question_with_all_candidates():
    result = interpret_question("Show me total sales.", user_id="user-123")

    assert result["status"] == "ambiguous"
    assert set(result["interpretations"]) == {"listing", "sum"}


def test_interpret_question_flags_unrecognized_question():
    result = interpret_question(
        "What's the weather like today?", user_id="user-123"
    )

    assert result["status"] == "unrecognized"
    assert result["interpretations"] == []


def test_interpret_question_raises_on_unsupported_language():
    with pytest.raises(UnsupportedLanguageError):
        interpret_question("¿Cuál es el promedio de ventas?", user_id="user-123")


def test_interpret_question_raises_on_timeout():
    with patch(
        "question_interpreter._match_intents",
        side_effect=lambda q: time.sleep(0.01) or ["average"],
    ):
        with patch("question_interpreter.QUESTION_INTERPRETATION_TIMEOUT_SECONDS", 0):
            with pytest.raises(QuestionInterpretationTimeoutError):
                interpret_question("What is the average?", user_id="user-123")


def test_interpret_question_logs_question_with_user_and_timestamp(caplog):
    question = "How many orders were placed?"

    with caplog.at_level(logging.INFO, logger="question_interpreter"):
        interpret_question(question, user_id="user-123")

    assert len(caplog.records) == 1
    logged = json.loads(caplog.records[0].message)
    assert logged["event"] == "question_asked"
    assert logged["user_id"] == "user-123"
    assert logged["question"] == question
    # Fails loudly if "timestamp" is missing or not a real ISO-8601 datetime,
    # rather than silently accepting any string in that field.
    datetime.fromisoformat(logged["timestamp"])
