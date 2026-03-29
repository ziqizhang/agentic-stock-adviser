"""Tests for SSE event types and serialisation."""

import json

from stock_adviser.events.types import (
    ChartUpdate,
    ReportUpdate,
    SSEEvent,
    StockOpened,
    TableUpdate,
    Token,
    ToolResult,
    ToolStart,
)


class TestSSEEventSerialisation:
    def test_token_event_to_sse(self):
        event = Token(content="Hello")
        result = event.to_sse()
        assert result["event"] == "message"
        data = json.loads(result["data"])
        assert data["type"] == "token"
        assert data["data"]["content"] == "Hello"

    def test_tool_start_event_to_sse(self):
        event = ToolStart(tool="get_stock_price", status="Fetching the latest price...")
        result = event.to_sse()
        data = json.loads(result["data"])
        assert data["type"] == "tool_start"
        assert data["data"]["tool"] == "get_stock_price"
        assert data["data"]["status"] == "Fetching the latest price..."

    def test_tool_result_event_to_sse(self):
        event = ToolResult()
        result = event.to_sse()
        data = json.loads(result["data"])
        assert data["type"] == "tool_result"

    def test_stock_opened_event_to_sse(self):
        event = StockOpened(symbol="AAPL", name="Apple Inc.")
        result = event.to_sse()
        data = json.loads(result["data"])
        assert data["type"] == "stock_opened"
        assert data["data"]["symbol"] == "AAPL"
        assert data["data"]["name"] == "Apple Inc."

    def test_chart_update_event_to_sse(self):
        event = ChartUpdate(symbol="AAPL", prices=[100.0, 101.5, 99.8], period="1y")
        result = event.to_sse()
        data = json.loads(result["data"])
        assert data["type"] == "chart_update"
        assert data["data"]["symbol"] == "AAPL"
        assert data["data"]["prices"] == [100.0, 101.5, 99.8]

    def test_table_update_event_to_sse(self):
        metrics = {"pe_ratio": 31.5, "eps": 7.91}
        event = TableUpdate(symbol="AAPL", metrics=metrics)
        result = event.to_sse()
        data = json.loads(result["data"])
        assert data["type"] == "table_update"
        assert data["data"]["metrics"]["pe_ratio"] == 31.5

    def test_report_update_event_to_sse(self):
        event = ReportUpdate(symbol="AAPL", markdown="## Analysis\nLooks good.")
        result = event.to_sse()
        data = json.loads(result["data"])
        assert data["type"] == "report_update"
        assert "## Analysis" in data["data"]["markdown"]

    def test_all_events_are_sse_event_subclasses(self):
        classes = [Token, ToolStart, ToolResult, StockOpened, ChartUpdate, TableUpdate, ReportUpdate]
        for cls in classes:
            assert issubclass(cls, SSEEvent)
