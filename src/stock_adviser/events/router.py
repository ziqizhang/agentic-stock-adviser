"""Route tool results to dashboard SSE events.

Maps each tool's output to the appropriate dashboard event type.
New tools are added by adding a handler function and registering it in _HANDLERS.

StockOpened is auto-prepended by route_tool_result whenever a handler returns
events that carry a symbol — individual handlers should NOT emit it themselves.
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
    prices = data.get("history_prices") or [data.get("price", 0.0)]
    period = data.get("history_period", "latest")
    return [
        ChartUpdate(
            symbol=data["symbol"],
            prices=prices,
            period=period,
        ),
    ]


def _handle_fundamentals(data: dict) -> list[SSEEvent]:
    symbol = data["symbol"]
    metrics = {k: v for k, v in data.items() if k != "symbol"}
    return [TableUpdate(symbol=symbol, metrics=metrics)]


_HANDLERS: dict[str, Callable[[dict], list[SSEEvent]]] = {
    "search_ticker": _handle_search_ticker,
    "get_stock_price": _handle_stock_price,
    "get_fundamentals": _handle_fundamentals,
}


def route_tool_result(tool_name: str, tool_content: str) -> list[SSEEvent]:
    """Convert a tool's string output to dashboard SSE events.

    Returns an empty list if the tool has no handler, the content contains
    an error, or the content is not valid JSON.

    Auto-prepends a StockOpened event when the first handler event carries a
    symbol field, ensuring the frontend always has a tab open before receiving
    data events. search_ticker is excluded because it emits StockOpened itself
    (with the proper company name from the search result).
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

    events = handler(data)

    # Auto-prepend StockOpened for data handlers (not search_ticker,
    # which already emits its own StockOpened with the real company name).
    if events and tool_name != "search_ticker":
        first = events[0]
        if hasattr(first, "symbol"):
            events.insert(0, StockOpened(symbol=first.symbol, name=first.symbol))

    return events
