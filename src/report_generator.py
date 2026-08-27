import json
import logging
from datetime import datetime, timezone

from fpdf import FPDF

from explanation_generator import explain_results

logger = logging.getLogger(__name__)


def _build_pdf(text: str) -> bytes:
    pdf = FPDF()
    pdf.set_compression(False)
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 10, text)
    return bytes(pdf.output())


def _build_text(text: str) -> bytes:
    return text.encode("utf-8")


_FORMAT_BUILDERS = {
    "pdf": _build_pdf,
    "text": _build_text,
}


class UnsupportedFormatError(Exception):
    pass


class DataExportError(Exception):
    pass


class PermissionDeniedError(Exception):
    pass


def generate_report(
    report_format: str, results: dict, user_id: str, output_path: str = None
) -> bytes:
    logger.info(
        json.dumps(
            {
                "event": "report_requested",
                "user_id": user_id,
                "report_format": report_format,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    )

    if report_format not in _FORMAT_BUILDERS:
        raise UnsupportedFormatError(
            f"'{report_format}' is not a supported report format. "
            f"Supported formats: {sorted(_FORMAT_BUILDERS)}."
        )

    summary = explain_results(results, user_id)

    builder = _FORMAT_BUILDERS[report_format]
    try:
        report_bytes = builder(summary)
    except (UnicodeEncodeError, ValueError, RuntimeError) as e:
        raise DataExportError(f"Failed to export '{report_format}' report: {e}") from e

    if output_path is not None:
        try:
            with open(output_path, "wb") as f:
                f.write(report_bytes)
        except PermissionError as e:
            raise PermissionDeniedError(
                f"Permission denied writing report to '{output_path}': {e}"
            ) from e

    return report_bytes
