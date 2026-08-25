import json
import logging
from datetime import datetime
from unittest.mock import patch

import pytest

from csv_upload import CsvFormatError, CsvMissingHeadersError, CsvTooLargeError, analyze_csv


def test_analyze_csv_returns_detected_columns_and_datatypes(tmp_path):
    csv_file = tmp_path / "widgets.csv"
    csv_file.write_text("id,name,price\n1,Widget,9.99\n2,Gadget,14.99\n")

    result = analyze_csv(str(csv_file), user_id="user-123")

    assert result["columns"] == [
        {"name": "id", "dtype": "int"},
        {"name": "name", "dtype": "string"},
        {"name": "price", "dtype": "float"},
    ]


def test_analyze_csv_falls_back_to_string_for_mixed_column(tmp_path):
    csv_file = tmp_path / "mixed.csv"
    csv_file.write_text("value\n1\nnot-a-number\n3\n")

    result = analyze_csv(str(csv_file), user_id="user-123")

    assert result["columns"] == [{"name": "value", "dtype": "string"}]


def test_analyze_csv_reports_unknown_dtype_for_all_null_column(tmp_path):
    csv_file = tmp_path / "empty_column.csv"
    csv_file.write_text("id,note\n1,\n2,\n")

    result = analyze_csv(str(csv_file), user_id="user-123")

    assert result["columns"] == [
        {"name": "id", "dtype": "int"},
        {"name": "note", "dtype": "unknown"},
    ]


def test_analyze_csv_identifies_duplicate_records(tmp_path):
    csv_file = tmp_path / "widgets.csv"
    csv_file.write_text("id,name\n1,Widget\n2,Gadget\n1,Widget\n")

    result = analyze_csv(str(csv_file), user_id="user-123")

    assert result["duplicates"] == [{"id": "1", "name": "Widget"}]


def test_analyze_csv_reports_no_duplicates_when_all_rows_unique(tmp_path):
    csv_file = tmp_path / "widgets.csv"
    csv_file.write_text("id,name\n1,Widget\n2,Gadget\n")

    result = analyze_csv(str(csv_file), user_id="user-123")

    assert result["duplicates"] == []


def test_analyze_csv_counts_null_values_per_column(tmp_path):
    csv_file = tmp_path / "widgets.csv"
    csv_file.write_text("id,note\n1,\n2,has a note\n3,\n")

    result = analyze_csv(str(csv_file), user_id="user-123")

    assert result["null_counts"] == {"id": 0, "note": 2}


def test_analyze_csv_raises_on_file_too_large(tmp_path):
    csv_file = tmp_path / "widgets.csv"
    csv_file.write_text("id,name\n1,Widget\n")

    with patch("csv_upload.os.path.getsize", return_value=90 * 1024 * 1024):
        with pytest.raises(CsvTooLargeError, match="80"):
            analyze_csv(str(csv_file), user_id="user-123")


def test_analyze_csv_raises_on_missing_headers(tmp_path):
    csv_file = tmp_path / "empty.csv"
    csv_file.write_text("")

    with pytest.raises(CsvMissingHeadersError):
        analyze_csv(str(csv_file), user_id="user-123")


def test_analyze_csv_raises_on_format_error(tmp_path):
    csv_file = tmp_path / "broken.csv"
    csv_file.write_bytes(b"\xff\xfe\x00\x01broken-not-utf8")

    with pytest.raises(CsvFormatError):
        analyze_csv(str(csv_file), user_id="user-123")


def test_analyze_csv_logs_upload_with_user_and_file_metadata(tmp_path, caplog):
    csv_file = tmp_path / "widgets.csv"
    csv_file.write_text("id,name\n1,Widget\n")

    with caplog.at_level(logging.INFO, logger="csv_upload"):
        analyze_csv(str(csv_file), user_id="user-123")

    assert len(caplog.records) == 1
    logged = json.loads(caplog.records[0].message)
    assert logged["event"] == "csv_upload"
    assert logged["user_id"] == "user-123"
    assert logged["file_name"] == "widgets.csv"
    assert logged["file_size_bytes"] == csv_file.stat().st_size
    # Fails loudly if "timestamp" is missing or not a real ISO-8601 datetime,
    # rather than silently accepting any string in that field.
    datetime.fromisoformat(logged["timestamp"])
