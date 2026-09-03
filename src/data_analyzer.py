import json
import logging
import time
from datetime import datetime, timezone

from explanation_generator import explain_results
from question_interpreter import interpret_question

logger = logging.getLogger(__name__)

_AGGREGATORS = {
    "average": lambda values: sum(values) / len(values),
    "sum": sum,
    "count": len,
}

ANALYSIS_TIMEOUT_SECONDS = 5


class DataInconsistencyError(Exception):
    pass


class AnalysisTimeoutError(Exception):
    pass


class UnsupportedQueryTypeError(Exception):
    pass


def _group_values(data: list, metric: str, group_by: str) -> dict:
    groups: dict = {}
    for row in data:
        groups.setdefault(row[group_by], []).append(row[metric])
    return groups


def _validate_data(data: list, metric: str, group_by: str = None) -> None:
    if not data:
        raise DataInconsistencyError("No data rows were provided to analyze.")
    for row in data:
        if metric not in row:
            raise DataInconsistencyError(f"Row is missing '{metric}': {row!r}")
        if not isinstance(row[metric], (int, float)):
            raise DataInconsistencyError(
                f"'{metric}' value is not numeric: {row[metric]!r}"
            )
        if group_by is not None and group_by not in row:
            raise DataInconsistencyError(f"Row is missing '{group_by}': {row!r}")


def analyze_data(
    question: str, data: list, metric: str, user_id: str, group_by: str = None
) -> dict:
    # Whether the interpreter found no single clear intent at all (ambiguous/
    # unrecognized) or a confident intent this analyzer just doesn't compute
    # (comparison/listing), analyze_data can't proceed either way - one
    # failure path covers both, per the user's explicit choice.
    interpretation = interpret_question(question, user_id)
    if interpretation["status"] != "confident":
        raise UnsupportedQueryTypeError(
            f"Could not determine a single clear analysis type for this "
            f"question (interpreter status: {interpretation['status']})."
        )

    aggregation = interpretation["interpretations"][0]
    if aggregation not in _AGGREGATORS:
        raise UnsupportedQueryTypeError(
            f"'{aggregation}' is a recognized intent but not a supported "
            f"analysis type here. Supported types: {sorted(_AGGREGATORS)}."
        )

    _validate_data(data, metric, group_by)
    aggregator = _AGGREGATORS[aggregation]

    started_at = time.monotonic()
    values = [row[metric] for row in data]
    answer = aggregator(values)
    elapsed_seconds = time.monotonic() - started_at

    if elapsed_seconds > ANALYSIS_TIMEOUT_SECONDS:
        raise AnalysisTimeoutError(
            f"Analysis took {elapsed_seconds:.1f}s, which exceeds the "
            f"{ANALYSIS_TIMEOUT_SECONDS}s limit."
        )

    results = {"metric": metric, "aggregation": aggregation, "value": answer}
    if group_by is not None:
        groups = _group_values(data, metric, group_by)
        results["breakdown"] = [
            {"label": label, "value": aggregator(group_values)}
            for label, group_values in groups.items()
        ]

    explanation = explain_results(results, user_id)

    # Logged after computing the answer, not before like most other modules'
    # trust logs - the acceptance criterion for this story specifically
    # requires the answer itself in the log line, so there is nothing
    # meaningful to log until the analysis has actually produced one.
    logger.info(
        json.dumps(
            {
                "event": "analysis_answered",
                "user_id": user_id,
                "question": question,
                "answer": answer,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    )

    return {"answer": answer, "explanation": explanation}
