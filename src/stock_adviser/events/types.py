"""Typed SSE events for the dashboard.

Each event knows how to serialise itself to the SSE wire format:
{"event": "message", "data": '{"type": "...", "data": {...}}'}
"""

import json
from dataclasses import dataclass, fields


@dataclass
class SSEEvent:
    """Base class for all SSE events. Subclasses define the payload fields."""

    event_type: str = ""

    def to_sse(self) -> dict[str, str]:
        """Convert to sse-starlette format: {"event": "message", "data": "<json>"}."""
        payload = {f.name: getattr(self, f.name) for f in fields(self) if f.name != "event_type"}
        data = json.dumps({"type": self.event_type, "data": payload})
        return {"event": "message", "data": data}


@dataclass
class Token(SSEEvent):
    content: str = ""
    event_type: str = "token"


@dataclass
class ToolStart(SSEEvent):
    tool: str = ""
    status: str = ""
    event_type: str = "tool_start"


@dataclass
class ToolResult(SSEEvent):
    event_type: str = "tool_result"


@dataclass
class StockOpened(SSEEvent):
    symbol: str = ""
    name: str = ""
    event_type: str = "stock_opened"


@dataclass
class ChartUpdate(SSEEvent):
    symbol: str = ""
    prices: list[float] | None = None
    period: str = ""
    event_type: str = "chart_update"

    def to_sse(self) -> dict[str, str]:
        payload = {"symbol": self.symbol, "prices": self.prices or [], "period": self.period}
        data = json.dumps({"type": self.event_type, "data": payload})
        return {"event": "message", "data": data}


@dataclass
class TableUpdate(SSEEvent):
    symbol: str = ""
    metrics: dict | None = None
    event_type: str = "table_update"

    def to_sse(self) -> dict[str, str]:
        payload = {"symbol": self.symbol, "metrics": self.metrics or {}}
        data = json.dumps({"type": self.event_type, "data": payload})
        return {"event": "message", "data": data}


@dataclass
class ReportUpdate(SSEEvent):
    symbol: str = ""
    markdown: str = ""
    event_type: str = "report_update"


@dataclass
class Done(SSEEvent):
    event_type: str = "done"
