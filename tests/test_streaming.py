"""Tests for streaming event classification."""

from stock_adviser.streaming import ToolResultEvent


class TestToolResultEvent:
    def test_has_tool_name_field(self):
        event = ToolResultEvent(tool_name="get_stock_price", content='{"symbol": "AAPL"}')
        assert event.tool_name == "get_stock_price"
        assert event.content == '{"symbol": "AAPL"}'

    def test_backward_compatible_defaults(self):
        event = ToolResultEvent()
        assert event.tool_name == ""
        assert event.content == ""
