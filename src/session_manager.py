import json
import logging
from datetime import datetime, timezone

from question_interpreter import interpret_question

logger = logging.getLogger(__name__)

_SESSIONS: dict = {}

SESSION_TIMEOUT_SECONDS = 1800  # 30 minutes


class ContextLossError(Exception):
    pass


def ask_follow_up(session_id: str, question: str, user_id: str) -> dict:
    logger.info(
        json.dumps(
            {
                "event": "follow_up_asked",
                "user_id": user_id,
                "session_id": session_id,
                "question": question,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    )

    # Only "ambiguous" (multiple conflicting intents) is rejected here, not
    # "unrecognized" - a genuine follow-up ("and last quarter?") often has no
    # standalone keyword of its own, since it leans on the prior context to
    # mean anything at all. Treating that as an error would break the normal
    # elliptical-follow-up case this whole story exists to support.
    interpretation = interpret_question(question, user_id)
    if interpretation["status"] == "ambiguous":
        return {
            "status": "ambiguous_follow_up",
            "interpretations": interpretation["interpretations"],
        }

    now = datetime.now(timezone.utc)

    if session_id not in _SESSIONS:
        _SESSIONS[session_id] = {"history": [question], "last_active": now}
        return {"status": "context_required", "history": [question]}

    session = _SESSIONS[session_id]

    if not session.get("history"):
        raise ContextLossError(
            f"Session '{session_id}' exists but its stored context is missing "
            f"or empty."
        )

    elapsed_seconds = (now - session["last_active"]).total_seconds()
    if elapsed_seconds > SESSION_TIMEOUT_SECONDS:
        _SESSIONS[session_id] = {"history": [question], "last_active": now}
        return {"status": "session_expired", "history": [question]}

    session["history"].append(question)
    session["last_active"] = now

    return {"status": "ok", "history": list(session["history"])}
