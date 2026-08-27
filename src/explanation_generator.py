import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_AGGREGATION_TEMPLATES = {
    "average": "The average {metric} is {value}.",
    "sum": "The total {metric} is {value}.",
    "count": "There are {value} {metric}.",
}

TOP_BREAKDOWN_ITEMS = 3
MAX_BREAKDOWN_ITEMS = 1000


class MisinterpretationError(Exception):
    pass


class ComplexityOverloadError(Exception):
    pass


class LanguageBarrierError(Exception):
    pass


def _is_unsupported_language(text: str) -> bool:
    return any(ord(char) > 127 for char in text)


def _format_value(value) -> str:
    if isinstance(value, float):
        return f"{value:,.2f}"
    return f"{value:,}"


def _join_with_and(items: list) -> str:
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return " and ".join(items)
    return ", ".join(items[:-1]) + ", and " + items[-1]


def _summarize_breakdown(breakdown: list) -> str:
    sorted_items = sorted(breakdown, key=lambda item: item["value"], reverse=True)
    top_items = sorted_items[:TOP_BREAKDOWN_ITEMS]
    remaining = len(sorted_items) - len(top_items)

    formatted_items = [
        f"{item['label']} ({_format_value(item['value'])})" for item in top_items
    ]
    items_text = _join_with_and(formatted_items)

    if remaining > 0:
        return f" The top contributors are {items_text}, with {remaining} more categories not shown."
    return f" The top contributors are {items_text}."


def explain_results(results: dict, user_id: str) -> str:
    logger.info(
        json.dumps(
            {
                "event": "explanation_requested",
                "user_id": user_id,
                "metric": results.get("metric"),
                "aggregation": results.get("aggregation"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    )

    missing_keys = [k for k in ("metric", "aggregation", "value") if k not in results]
    if missing_keys:
        raise MisinterpretationError(
            f"Cannot interpret analytical results: missing required key(s) "
            f"{missing_keys}."
        )

    metric = results["metric"]
    aggregation = results["aggregation"]
    value = results["value"]

    if aggregation not in _AGGREGATION_TEMPLATES:
        raise MisinterpretationError(
            f"'{aggregation}' is not a recognized aggregation type. "
            f"Supported types: {sorted(_AGGREGATION_TEMPLATES)}."
        )

    if _is_unsupported_language(metric):
        raise LanguageBarrierError(
            f"Metric name contains non-ASCII characters, which this "
            f"English-template generator cannot phrase correctly: {metric!r}"
        )

    breakdown = results.get("breakdown")
    if breakdown:
        if len(breakdown) > MAX_BREAKDOWN_ITEMS:
            raise ComplexityOverloadError(
                f"Breakdown has {len(breakdown)} entries, which exceeds the "
                f"{MAX_BREAKDOWN_ITEMS}-entry limit this generator can summarize."
            )
        for item in breakdown:
            if _is_unsupported_language(item["label"]):
                raise LanguageBarrierError(
                    f"Breakdown label contains non-ASCII characters, which this "
                    f"English-template generator cannot phrase correctly: "
                    f"{item['label']!r}"
                )

    template = _AGGREGATION_TEMPLATES[aggregation]
    summary = template.format(metric=metric, value=_format_value(value))

    if breakdown:
        summary += _summarize_breakdown(breakdown)

    return summary
