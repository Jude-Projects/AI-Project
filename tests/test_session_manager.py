import json
import logging
from datetime import datetime, timedelta, timezone

import pytest

import session_manager
from session_manager import ContextLossError, ask_follow_up


def test_ask_follow_up_prompts_for_context_on_new_session():
    result = ask_follow_up(
        "session-new-1", "What is the average revenue?", user_id="user-123"
    )

    assert result["status"] == "context_required"
    assert result["history"] == ["What is the average revenue?"]


def test_ask_follow_up_remembers_context_on_existing_session():
    session_id = "session-existing-1"
    ask_follow_up(session_id, "What is the average revenue?", user_id="user-123")

    result = ask_follow_up(session_id, "And what about last quarter?", user_id="user-123")

    assert result["status"] == "ok"
    assert result["history"] == [
        "What is the average revenue?",
        "And what about last quarter?",
    ]


def test_ask_follow_up_flags_ambiguous_follow_up_without_storing_it():
    session_id = "session-ambiguous-1"

    result = ask_follow_up(session_id, "Show me total sales.", user_id="user-123")

    assert result["status"] == "ambiguous_follow_up"
    assert set(result["interpretations"]) == {"listing", "sum"}

    # The rejected question must not have started/extended the session's context.
    follow_up = ask_follow_up(
        session_id, "What is the average revenue?", user_id="user-123"
    )
    assert follow_up["status"] == "context_required"
    assert follow_up["history"] == ["What is the average revenue?"]


def test_ask_follow_up_expires_stale_session_and_restarts_context():
    session_id = "session-stale-1"
    ask_follow_up(session_id, "What is the average revenue?", user_id="user-123")

    # Simulate a session that has sat idle past the timeout window.
    stale_time = datetime.now(timezone.utc) - timedelta(
        seconds=session_manager.SESSION_TIMEOUT_SECONDS + 1
    )
    session_manager._SESSIONS[session_id]["last_active"] = stale_time

    result = ask_follow_up(session_id, "What is the total sum?", user_id="user-123")

    assert result["status"] == "session_expired"
    assert result["history"] == ["What is the total sum?"]


def test_ask_follow_up_raises_on_context_loss():
    session_id = "session-corrupted-1"
    ask_follow_up(session_id, "What is the average revenue?", user_id="user-123")

    # Simulate internal corruption: the session is registered but its history
    # is gone, which should never happen through normal use of this module.
    session_manager._SESSIONS[session_id]["history"] = []

    with pytest.raises(ContextLossError):
        ask_follow_up(session_id, "What is the total sum?", user_id="user-123")


def test_ask_follow_up_logs_request_with_user_session_and_question(caplog):
    with caplog.at_level(logging.INFO, logger="session_manager"):
        ask_follow_up(
            "session-log-1", "What is the average revenue?", user_id="user-123"
        )

    assert len(caplog.records) == 1
    logged = json.loads(caplog.records[0].message)
    assert logged["event"] == "follow_up_asked"
    assert logged["user_id"] == "user-123"
    assert logged["session_id"] == "session-log-1"
    assert logged["question"] == "What is the average revenue?"
    # Fails loudly if "timestamp" is missing or not a real ISO-8601 datetime,
    # rather than silently accepting any string in that field.
    datetime.fromisoformat(logged["timestamp"])
