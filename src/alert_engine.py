import json
import logging
from datetime import datetime, timezone

from data_analyzer import DataInconsistencyError, UnsupportedQueryTypeError, analyze_data

logger = logging.getLogger(__name__)

MIN_SAMPLE_SIZE = 3


class RecommendationError(Exception):
    pass


def _evaluate_rule(rule: dict, user_id: str) -> dict:
    name = rule["name"]
    metric = rule["metric"]
    aggregation = rule["aggregation"]
    threshold = rule["threshold"]
    condition = rule["condition"]
    data = rule["data"]

    # A rule evaluated against too few data points is exactly how a
    # rule-based engine produces a false positive - one unlucky row looking
    # like a trend. Skip rather than risk alerting on statistical noise.
    if len(data) < MIN_SAMPLE_SIZE:
        return {
            "name": name,
            "status": "insufficient_data",
            "message": (
                f"'{name}' has only {len(data)} data point(s); at least "
                f"{MIN_SAMPLE_SIZE} are required to evaluate reliably."
            ),
        }

    question = f"What is the {aggregation} {metric}?"
    try:
        result = analyze_data(question, data, metric, user_id)
    except (DataInconsistencyError, UnsupportedQueryTypeError) as e:
        # One broken rule should never silently stop the rest from being
        # evaluated - that would genuinely miss whatever alerts they'd have
        # raised.
        return {"name": name, "status": "evaluation_error", "message": str(e)}

    value = result["answer"]

    if condition == "above":
        triggered = value > threshold
    else:
        triggered = value < threshold

    alert = {
        "name": name,
        "metric": metric,
        "condition": condition,
        "value": value,
        "threshold": threshold,
    }

    if triggered:
        alert["status"] = "triggered"
        alert["message"] = (
            f"'{name}' triggered: {metric} is {value}, which is {condition} "
            f"the threshold of {threshold}."
        )
    else:
        alert["status"] = "not_triggered"

    return alert


def generate_alerts(rules: list, user_id: str) -> list:
    logger.info(
        json.dumps(
            {
                "event": "alerts_requested",
                "user_id": user_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    )

    return [_evaluate_rule(rule, user_id) for rule in rules]


def generate_recommendation(alert: dict, user_id: str) -> str:
    logger.info(
        json.dumps(
            {
                "event": "recommendation_requested",
                "user_id": user_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    )

    if alert.get("status") != "triggered":
        raise RecommendationError(
            f"Cannot recommend an action for an alert with status "
            f"'{alert.get('status')}' - only a triggered alert has "
            f"something actionable to recommend."
        )

    required_keys = ("name", "metric", "value", "condition", "threshold")
    missing = [key for key in required_keys if key not in alert]
    if missing:
        raise RecommendationError(
            f"Alert is missing required field(s) for a recommendation: {missing}."
        )

    return (
        f"Recommended action: review recent activity related to "
        f"'{alert['name']}', since {alert['metric']} ({alert['value']}) is "
        f"{alert['condition']} the threshold of {alert['threshold']}."
    )
