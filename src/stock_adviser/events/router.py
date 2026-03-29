"""Route tool results to dashboard SSE events.

Maps each tool's output to the appropriate dashboard event type.
New tools are added by adding a handler function and registering it in _HANDLERS.
"""

import json
from collections.abc import Callable

from stock_adviser.events.types import ChartUpdate, SSEEvent, StockOpened, TableUpdate


def _handle_search_ticker(data: dict) -> list[SSEEvent]:
    matches = data.get("matches", [])
    if not matches:
        return []
    first = matches[0]
    return [StockOpened(symbol=first["symbol"], name=first.get("name", ""))]


def _handle_stock_price(data: dict) -> list[SSEEvent]:
    return [
        ChartUpdate(
            symbol=data["symbol"],
            prices=[data.get("price", 0.0)],
            period="latest",
        )
    ]


def _handle_fundamentals(data: dict) -> list[SSEEvent]:
    symbol = data.pop("symbol")
    return [TableUpdate(symbol=symbol, metrics=data)]


_HANDLERS: dict[str, Callable[[dict], list[SSEEvent]]] = {
    "search_ticker": _handle_search_ticker,
    "get_stock_price": _handle_stock_price,
    "get_fundamentals": _handle_fundamentals,
}


def route_tool_result(tool_name: str, tool_content: str) -> list[SSEEvent]:
    """Convert a tool's string output to dashboard SSE events.

    Returns an empty list if the tool has no handler, the content contains
    an error, or the content is not valid JSON.
    """
    handler = _HANDLERS.get(tool_name)
    if not handler:
        return []

    try:
        data = json.loads(tool_content)
    except (json.JSONDecodeError, TypeError):
        return []

    if "error" in data:
        return []

    return handler(data)
