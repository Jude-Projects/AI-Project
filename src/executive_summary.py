import json
import logging
import time
from datetime import datetime, timezone

from data_analyzer import DataInconsistencyError, UnsupportedQueryTypeError, analyze_data

logger = logging.getLogger(__name__)

SUMMARY_TIMEOUT_SECONDS = 10


class SummaryGenerationTimeoutError(Exception):
    pass


def generate_executive_summary(kpis: list, user_id: str) -> dict:
    logger.info(
        json.dumps(
            {
                "event": "executive_summary_requested",
                "user_id": user_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    )

    started_at = time.monotonic()
    kpi_results = {}
    for kpi in kpis:
        name = kpi["name"]
        metric = kpi["metric"]
        aggregation = kpi["aggregation"]
        data = kpi["data"]

        if not data:
            kpi_results[name] = {
                "status": "missing_data",
                "message": f"No data was provided for '{name}'.",
            }
            continue

        question = f"What is the {aggregation} {metric}?"
        try:
            result = analyze_data(question, data, metric, user_id)
        except (DataInconsistencyError, UnsupportedQueryTypeError) as e:
            # One broken KPI should never take down the whole summary - an
            # executive still wants everything else that could be computed.
            kpi_results[name] = {"status": "calculation_error", "message": str(e)}
            continue

        kpi_results[name] = {
            "status": "ok",
            "answer": result["answer"],
            "explanation": result["explanation"],
        }

    elapsed_seconds = time.monotonic() - started_at
    if elapsed_seconds > SUMMARY_TIMEOUT_SECONDS:
        raise SummaryGenerationTimeoutError(
            f"Generating the summary took {elapsed_seconds:.1f}s, which "
            f"exceeds the {SUMMARY_TIMEOUT_SECONDS}s limit."
        )

    successful = sum(1 for r in kpi_results.values() if r["status"] == "ok")
    failed = len(kpis) - successful
    if failed == 0:
        summary = f"Generated {successful} of {len(kpis)} KPIs successfully."
    else:
        summary = (
            f"Generated {successful} of {len(kpis)} KPIs successfully; "
            f"{failed} could not be computed."
        )

    return {"summary": summary, "kpis": kpi_results}
