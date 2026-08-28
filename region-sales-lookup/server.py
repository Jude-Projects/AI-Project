"""MCP server for the AI Data Assistant: exposes regional sales data
the assistant has no other way to see."""

from typing import Annotated

from mcp.server.mcpserver import MCPServer
from pydantic import Field

mcp = MCPServer("region-sales-lookup")

SALES_RECORDS = [
    {"region": "northeast", "product": "Widget Pro", "total_sales_usd": 1_200_000, "yoy_growth_pct": 8},
    {"region": "northeast", "product": "Widget Standard", "total_sales_usd": 410_000, "yoy_growth_pct": 2},
    {"region": "midwest", "product": "Widget Standard", "total_sales_usd": 860_000, "yoy_growth_pct": 3},
    {"region": "midwest", "product": "Widget Pro", "total_sales_usd": 305_000, "yoy_growth_pct": -1},
    {"region": "west", "product": "Widget Pro", "total_sales_usd": 2_100_000, "yoy_growth_pct": 15},
    {"region": "west", "product": "Widget Max", "total_sales_usd": 640_000, "yoy_growth_pct": 22},
    {"region": "south", "product": "Widget Max", "total_sales_usd": 1_500_000, "yoy_growth_pct": 6},
    {"region": "south", "product": "Widget Standard", "total_sales_usd": 275_000, "yoy_growth_pct": 4},
]


@mcp.tool()
def search_region_sales(
    query: Annotated[str, Field(min_length=1, max_length=100)],
    limit: Annotated[int, Field(ge=1, le=20)] = 5,
) -> list[dict]:
    """Call this whenever the user asks about sales performance, revenue,
    or year-over-year growth for a US sales region or product - e.g.
    "how is the west region doing" or "sales for Widget Pro". Do not
    guess or estimate sales figures from general knowledge; always call
    this tool to get real numbers. The query is matched case-insensitively
    as a substring against region and product names; results are capped
    at `limit` rows."""
    needle = query.strip().lower()
    matches = [
        row
        for row in SALES_RECORDS
        if needle in row["region"] or needle in row["product"].lower()
    ]
    return matches[:limit]


if __name__ == "__main__":
    mcp.run(transport="stdio")
