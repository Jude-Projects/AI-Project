import json
import logging
from datetime import datetime
from unittest.mock import patch

import pytest

import report_generator
from report_generator import (
    DataExportError,
    PermissionDeniedError,
    UnsupportedFormatError,
    generate_report,
)


def test_generate_report_returns_pdf_with_explanation_text():
    results = {"metric": "revenue", "aggregation": "average", "value": 45231.5}

    pdf_bytes = generate_report("pdf", results, user_id="user-123")

    assert pdf_bytes.startswith(b"%PDF")
    assert b"average revenue" in pdf_bytes
    assert b"45,231.50" in pdf_bytes


def test_generate_report_returns_plain_text_for_text_format():
    results = {"metric": "revenue", "aggregation": "average", "value": 45231.5}

    report_bytes = generate_report("text", results, user_id="user-123")

    assert report_bytes == b"The average revenue is 45,231.50."


def test_generate_report_uses_distinct_output_per_format():
    results = {"metric": "revenue", "aggregation": "average", "value": 45231.5}

    pdf_bytes = generate_report("pdf", results, user_id="user-123")
    text_bytes = generate_report("text", results, user_id="user-123")

    assert pdf_bytes.startswith(b"%PDF") and b"average revenue" in pdf_bytes
    assert not text_bytes.startswith(b"%PDF") and b"average revenue" in text_bytes


def test_generate_report_raises_on_unsupported_format():
    results = {"metric": "revenue", "aggregation": "average", "value": 45231.5}

    with pytest.raises(UnsupportedFormatError):
        generate_report("docx", results, user_id="user-123")


def test_generate_report_raises_on_data_export_error():
    results = {"metric": "revenue", "aggregation": "average", "value": 45231.5}

    def _broken_builder(text):
        raise ValueError("simulated export failure")

    with patch.dict(report_generator._FORMAT_BUILDERS, {"pdf": _broken_builder}):
        with pytest.raises(DataExportError):
            generate_report("pdf", results, user_id="user-123")


def test_generate_report_raises_on_permission_denied_writing_output():
    results = {"metric": "revenue", "aggregation": "average", "value": 45231.5}

    with patch("builtins.open", side_effect=PermissionError("denied")):
        with pytest.raises(PermissionDeniedError):
            generate_report(
                "text",
                results,
                user_id="user-123",
                output_path="/some/protected/report.txt",
            )


def test_generate_report_logs_request_with_user_and_format(caplog):
    results = {"metric": "revenue", "aggregation": "average", "value": 45231.5}

    with caplog.at_level(logging.INFO, logger="report_generator"):
        generate_report("pdf", results, user_id="user-123")

    assert len(caplog.records) == 1
    logged = json.loads(caplog.records[0].message)
    assert logged["event"] == "report_requested"
    assert logged["user_id"] == "user-123"
    assert logged["report_format"] == "pdf"
    # Fails loudly if "timestamp" is missing or not a real ISO-8601 datetime,
    # rather than silently accepting any string in that field.
    datetime.fromisoformat(logged["timestamp"])
