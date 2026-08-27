import json
import logging
import time
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

INTENT_KEYWORDS = {
    "average": ["average", "avg", "mean"],
    "sum": ["sum", "total"],
    "count": ["count", "how many", "number of"],
    "comparison": ["compare", "versus", " vs ", "vs.", "difference between"],
    "listing": ["show", "list", "display"],
}

QUESTION_INTERPRETATION_TIMEOUT_SECONDS = 5


class UnsupportedLanguageError(Exception):
    pass


class QuestionInterpretationTimeoutError(Exception):
    pass


def _is_unsupported_language(question: str) -> bool:
    return any(ord(char) > 127 for char in question)


def _match_intents(question: str) -> list:
    lowered = question.lower()
    return [
        intent
        for intent, keywords in INTENT_KEYWORDS.items()
        if any(keyword in lowered for keyword in keywords)
    ]


def interpret_question(question: str, user_id: str) -> dict:
    logger.info(
        json.dumps(
            {
                "event": "question_asked",
                "user_id": user_id,
                "question": question,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    )

    if _is_unsupported_language(question):
        raise UnsupportedLanguageError(
            f"Question contains non-ASCII characters, which this keyword-based "
            f"parser cannot interpret: {question!r}"
        )

    # Measured after the call completes, not preemptive - fine for this
    # in-process keyword matcher, but will need a real request timeout once
    # this is backed by an external NLU call.
    started_at = time.monotonic()
    matched = _match_intents(question)
    elapsed_seconds = time.monotonic() - started_at

    if elapsed_seconds > QUESTION_INTERPRETATION_TIMEOUT_SECONDS:
        raise QuestionInterpretationTimeoutError(
            f"Interpreting the question took {elapsed_seconds:.1f}s, which "
            f"exceeds the {QUESTION_INTERPRETATION_TIMEOUT_SECONDS}s limit."
        )

    if len(matched) == 1:
        status = "confident"
    elif len(matched) == 0:
        status = "unrecognized"
    else:
        status = "ambiguous"

    return {"question": question, "status": status, "interpretations": matched}
