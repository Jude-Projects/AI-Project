import json
import logging
from datetime import datetime

import pytest

from visualization import (
    D3_CDN_URL,
    DataMismatchError,
    UnsupportedChartTypeError,
    VisualizationRenderingError,
    generate_visualization,
)


def test_generate_visualization_returns_bar_chart_html():
    data = [{"label": "Q1", "value": 10}, {"label": "Q2", "value": 20}]

    html = generate_visualization("bar", data, user_id="user-123")

    assert D3_CDN_URL in html
    assert 'id="chart"' in html
    assert "scaleBand" in html  # bar-chart-specific marker
    assert json.dumps(data) in html


def test_generate_visualization_returns_line_chart_html():
    data = [{"label": "Q1", "value": 10}, {"label": "Q2", "value": 20}]

    html = generate_visualization("line", data, user_id="user-123")

    assert D3_CDN_URL in html
    assert "d3.line()" in html  # line-chart-specific marker
    assert json.dumps(data) in html


def test_generate_visualization_uses_distinct_markup_per_chart_type():
    data = [{"label": "Q1", "value": 10}]

    bar_html = generate_visualization("bar", data, user_id="user-123")
    line_html = generate_visualization("line", data, user_id="user-123")

    assert "scaleBand" in bar_html and "d3.line()" not in bar_html
    assert "d3.line()" in line_html and "scaleBand" not in line_html


def test_generate_visualization_raises_on_unsupported_chart_type():
    with pytest.raises(UnsupportedChartTypeError):
        generate_visualization(
            "pie", [{"label": "Q1", "value": 10}], user_id="user-123"
        )


def test_generate_visualization_raises_on_empty_data():
    with pytest.raises(DataMismatchError):
        generate_visualization("bar", [], user_id="user-123")


def test_generate_visualization_raises_on_data_missing_required_keys():
    with pytest.raises(DataMismatchError):
        generate_visualization("bar", [{"label": "Q1"}], user_id="user-123")


def test_generate_visualization_raises_on_rendering_error_for_unserializable_value():
    with pytest.raises(VisualizationRenderingError):
        generate_visualization(
            "bar", [{"label": "Q1", "value": {1, 2, 3}}], user_id="user-123"
        )


def test_generate_visualization_logs_request_with_user_and_chart_type(caplog):
    with caplog.at_level(logging.INFO, logger="visualization"):
        generate_visualization(
            "bar", [{"label": "Q1", "value": 10}], user_id="user-123"
        )

    assert len(caplog.records) == 1
    logged = json.loads(caplog.records[0].message)
    assert logged["event"] == "visualization_requested"
    assert logged["user_id"] == "user-123"
    assert logged["chart_type"] == "bar"
    # Fails loudly if "timestamp" is missing or not a real ISO-8601 datetime,
    # rather than silently accepting any string in that field.
    datetime.fromisoformat(logged["timestamp"])
