"""Tests for graph structure and routing logic."""

from langchain_core.messages import AIMessage
from langgraph.graph import END

from stock_adviser.graph import should_continue


class TestShouldContinue:
    def test_routes_to_tools_when_tool_calls_present(self):
        msg = AIMessage(content="", tool_calls=[{"name": "get_stock_price", "args": {"symbol": "AAPL"}, "id": "1"}])
        result = should_continue({"messages": [msg]})
        assert result == "tools"

    def test_routes_to_end_when_no_tool_calls(self):
        msg = AIMessage(content="Here are the results.")
        result = should_continue({"messages": [msg]})
        assert result == END

    def test_routes_to_end_with_empty_tool_calls(self):
        msg = AIMessage(content="Done.", tool_calls=[])
        result = should_continue({"messages": [msg]})
        assert result == END


class TestGraphStructure:
    def test_graph_has_expected_nodes(self):
        from stock_adviser.graph import graph

        node_names = set(graph.get_graph().nodes.keys())
        assert "agent" in node_names
        assert "tools" in node_names

    def test_graph_is_compiled(self):
        from stock_adviser.graph import graph

        # A compiled graph has an invoke method
        assert callable(getattr(graph, "invoke", None))
