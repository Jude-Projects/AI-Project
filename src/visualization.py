import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

D3_CDN_URL = "https://d3js.org/d3.v7.min.js"

_CHART_TEMPLATES = {
    "bar": """
        const svg = d3.select("#chart").append("svg")
            .attr("width", 600)
            .attr("height", 400);

        const x = d3.scaleBand()
            .domain(data.map(d => d.label))
            .range([40, 580])
            .padding(0.2);

        const y = d3.scaleLinear()
            .domain([0, d3.max(data, d => d.value)])
            .range([360, 20]);

        svg.selectAll("rect")
            .data(data)
            .join("rect")
            .attr("x", d => x(d.label))
            .attr("y", d => y(d.value))
            .attr("width", x.bandwidth())
            .attr("height", d => 360 - y(d.value));
    """,
    "line": """
        const svg = d3.select("#chart").append("svg")
            .attr("width", 600)
            .attr("height", 400);

        const x = d3.scalePoint()
            .domain(data.map(d => d.label))
            .range([40, 580]);

        const y = d3.scaleLinear()
            .domain([0, d3.max(data, d => d.value)])
            .range([360, 20]);

        const line = d3.line()
            .x(d => x(d.label))
            .y(d => y(d.value));

        svg.append("path")
            .datum(data)
            .attr("fill", "none")
            .attr("stroke", "steelblue")
            .attr("d", line);
    """,
}


class UnsupportedChartTypeError(Exception):
    pass


class DataMismatchError(Exception):
    pass


class VisualizationRenderingError(Exception):
    pass


def _validate_data(data: list) -> None:
    if not isinstance(data, list) or not data:
        raise DataMismatchError("Chart data must be a non-empty list of records.")
    for record in data:
        if not isinstance(record, dict) or "label" not in record or "value" not in record:
            raise DataMismatchError(
                f"Each chart data record must be a dict with 'label' and 'value' "
                f"keys, got: {record!r}"
            )


def generate_visualization(chart_type: str, data: list, user_id: str) -> str:
    logger.info(
        json.dumps(
            {
                "event": "visualization_requested",
                "user_id": user_id,
                "chart_type": chart_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    )

    if chart_type not in _CHART_TEMPLATES:
        raise UnsupportedChartTypeError(
            f"'{chart_type}' is not a supported chart type. "
            f"Supported types: {sorted(_CHART_TEMPLATES)}."
        )

    _validate_data(data)

    try:
        chart_script = _CHART_TEMPLATES[chart_type]
        data_json = json.dumps(data)

        return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <script src="{D3_CDN_URL}"></script>
</head>
<body>
  <div id="chart"></div>
  <script>
    const data = {data_json};
    {chart_script}
  </script>
</body>
</html>"""
    except (TypeError, ValueError) as e:
        raise VisualizationRenderingError(
            f"Failed to render '{chart_type}' chart: {e}"
        ) from e
