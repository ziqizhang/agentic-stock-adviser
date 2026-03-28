from typing import Literal

from langchain_core.messages import SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from stock_adviser.llm import get_llm
from stock_adviser.prompts import SYSTEM_PROMPT
from stock_adviser.state import AgentState
from stock_adviser.tools.fundamentals import get_fundamentals
from stock_adviser.tools.price import get_stock_price
from stock_adviser.tools.search import search_ticker

tools = [search_ticker, get_stock_price, get_fundamentals]


def agent(state: AgentState) -> dict:
    """Call the LLM with tools bound. Prepend system prompt if this is the first turn."""
    llm = get_llm().bind_tools(tools)
    messages = state["messages"]
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT), *messages]
    response = llm.invoke(messages)
    return {"messages": [response]}


def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    """Route to tools if the last message has tool calls, otherwise end."""
    last = state["messages"][-1]
    if last.tool_calls:
        return "tools"
    return END


graph = (
    StateGraph(AgentState)
    .add_node("agent", agent)
    .add_node("tools", ToolNode(tools, handle_tool_errors=True))
    .add_edge(START, "agent")
    .add_conditional_edges("agent", should_continue, ["tools", END])
    .add_edge("tools", "agent")
    .compile()
)
