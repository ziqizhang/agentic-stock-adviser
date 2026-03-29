"""Tests for SSE event types and serialisation."""

import json

from stock_adviser.events.router import route_tool_result
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


class TestEventRouter:
    def test_routes_get_stock_price_to_chart_update(self):
        tool_content = json.dumps(
            {
                "symbol": "AAPL",
                "price": 248.80,
                "change_percent": -1.62,
                "market_cap": 3800000000000,
                "fifty_two_week_high": 260.0,
                "fifty_two_week_low": 164.0,
                "fifty_day_average": 240.0,
                "two_hundred_day_average": 220.0,
            }
        )
        events = route_tool_result("get_stock_price", tool_content)
        assert len(events) == 2
        assert isinstance(events[0], StockOpened)
        assert events[0].symbol == "AAPL"
        assert isinstance(events[1], ChartUpdate)
        assert events[1].symbol == "AAPL"

    def test_routes_get_fundamentals_to_table_update(self):
        tool_content = json.dumps(
            {
                "symbol": "AAPL",
                "pe_ratio": 31.5,
                "forward_pe": 28.0,
                "eps": 7.91,
                "revenue_growth": 0.157,
                "profit_margin": 0.27,
                "debt_to_equity": 1.5,
                "return_on_equity": 0.45,
                "dividend_yield": 0.005,
            }
        )
        events = route_tool_result("get_fundamentals", tool_content)
        assert len(events) == 2
        assert isinstance(events[0], StockOpened)
        assert events[0].symbol == "AAPL"
        assert isinstance(events[1], TableUpdate)
        assert events[1].symbol == "AAPL"
        assert events[1].metrics["pe_ratio"] == 31.5

    def test_routes_search_ticker_to_stock_opened(self):
        tool_content = json.dumps(
            {"query": "Apple", "matches": [{"symbol": "AAPL", "name": "Apple Inc.", "exchange": "NMS"}]}
        )
        events = route_tool_result("search_ticker", tool_content)
        assert len(events) == 1
        assert isinstance(events[0], StockOpened)
        assert events[0].symbol == "AAPL"
        assert events[0].name == "Apple Inc."

    def test_routes_search_ticker_no_matches_to_empty(self):
        tool_content = json.dumps({"query": "xyzxyz", "matches": []})
        events = route_tool_result("search_ticker", tool_content)
        assert events == []

    def test_routes_unknown_tool_to_empty(self):
        events = route_tool_result("unknown_tool", "{}")
        assert events == []

    def test_routes_tool_error_to_empty(self):
        tool_content = json.dumps({"error": "Ticker not found"})
        events = route_tool_result("get_stock_price", tool_content)
        assert events == []
