"""One complete Claude tool-use round trip for the AI Data Assistant
(answers customer questions about sales by region)."""

import json

import anthropic

MODEL = "claude-opus-5"

REGION_SALES = {
    "northeast": {"total_sales": "$1.2M", "top_product": "Widget Pro", "yoy_growth": "8%"},
    "midwest": {"total_sales": "$860K", "top_product": "Widget Standard", "yoy_growth": "3%"},
    "west": {"total_sales": "$2.1M", "top_product": "Widget Pro", "yoy_growth": "15%"},
    "south": {"total_sales": "$1.5M", "top_product": "Widget Max", "yoy_growth": "6%"},
}

GET_REGION_SALES_TOOL = {
    "name": "get_region_sales",
    "description": (
        "Look up total sales, top-selling product, and year-over-year growth "
        "for a given US sales region. Use this whenever the customer asks "
        "about sales performance, revenue, or growth in a specific region."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "region": {
                "type": "string",
                "description": "Sales region name, e.g. 'west', 'northeast', 'midwest', 'south'.",
            }
        },
        "required": ["region"],
    },
}


def get_region_sales(region: str) -> dict:
    key = region.strip().lower()
    if key not in REGION_SALES:
        return {"error": f"No sales data for region '{region}'."}
    return REGION_SALES[key]


def header(label: str) -> None:
    print(f"\n=== {label} ===")


def main() -> None:
    client = anthropic.Anthropic()
    user_question = "How are sales doing in the West region?"

    messages = [{"role": "user", "content": user_question}]
    request_kwargs = {
        "model": MODEL,
        "max_tokens": 1024,
        "tools": [GET_REGION_SALES_TOOL],
        "messages": messages,
    }

    header("1. REQUEST SENT")
    print(json.dumps(request_kwargs, indent=2))

    response = client.messages.create(**request_kwargs)

    header("2. STOP REASON")
    print(response.stop_reason)

    if response.stop_reason != "tool_use":
        header("FINAL ANSWER (no tool call made)")
        print(next(b.text for b in response.content if b.type == "text"))
        return

    tool_use_block = next(b for b in response.content if b.type == "tool_use")

    header("3. TOOL_USE BLOCK")
    print(json.dumps(
        {"id": tool_use_block.id, "name": tool_use_block.name, "input": tool_use_block.input},
        indent=2,
    ))

    header("4. MY FUNCTION EXECUTES")
    result = get_region_sales(**tool_use_block.input)  # <- local code runs here, not Claude
    print(f"get_region_sales({tool_use_block.input}) -> {result}")

    tool_result_block = {
        "type": "tool_result",
        "tool_use_id": tool_use_block.id,
        "content": json.dumps(result),
    }

    header("5. TOOL_RESULT SENT BACK")
    print(json.dumps(tool_result_block, indent=2))

    messages.append({"role": "assistant", "content": response.content})
    messages.append({"role": "user", "content": [tool_result_block]})

    final_response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        tools=[GET_REGION_SALES_TOOL],
        messages=messages,
    )

    header("6. FINAL ANSWER")
    print(next(b.text for b in final_response.content if b.type == "text"))


if __name__ == "__main__":
    main()
