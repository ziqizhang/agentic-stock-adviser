# Pillar 1: The Paradigm Shift — From Predefined Graphs to ReAct Agent Loops

> **Goal:** Build a single conversational agent with LLM-controlled flow via tool calling.
> **Patterns:** Tool Use (5), Planning (6)
> **Reference:** deep_research_from_scratch Notebooks 1-2, Deep Agents PDF

---

## What You Already Know vs. What's New

### In ai-genai-cam, you build graphs like this:

```python
# Graph shape is fixed at compile time
builder = StateGraph(CAMState)
builder.add_node("qa_generator", qa_generator_node)
builder.add_node("planner", planner_node)
builder.add_node("generator", generator_node)
builder.add_node("reviewer", reviewer_node)
builder.add_node("editor", editor_node)

builder.add_edge("qa_generator", "planner")
builder.add_edge("planner", "generator")
builder.add_edge("generator", "reviewer")
builder.add_conditional_edges("reviewer", route_after_review)  # fixed routing logic
builder.add_edge("editor", END)
```

The **developer** decides the flow. The LLM generates content within each node,
but it never chooses which node runs next.

### In a ReAct agent, the graph looks like this:

```python
# Graph shape is dynamic — the LLM decides the flow
builder = StateGraph(AgentState)
builder.add_node("agent", call_model)       # LLM with bound tools
builder.add_node("tools", tool_executor)    # Executes whatever tools LLM requested

builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", should_continue)  # Did LLM call tools or give final answer?
builder.add_edge("tools", "agent")                        # After tools, back to LLM
```

The graph is just **two nodes in a loop**. The LLM decides:
- Which tools to call (if any)
- What arguments to pass
- When it has enough information to answer
- When to ask the user for clarification

**This is the fundamental paradigm shift:** The LLM is the orchestrator, not the developer.

---

## The ReAct Loop Explained

```
User: "Is AAPL a good buy right now?"
    │
    ▼
┌─────────────────────────────────────────────────┐
│ AGENT NODE (LLM with tools bound)               │
│                                                  │
│ LLM thinks: "I need current price and           │
│ fundamentals to answer this."                    │
│                                                  │
│ Output: tool_calls=[                             │
│   {name: "get_stock_price", args: {symbol: "AAPL"}},  │
│   {name: "get_fundamentals", args: {symbol: "AAPL"}}  │
│ ]                                                │
└──────────────┬──────────────────────────────────┘
               │ (conditional edge: has tool_calls → tools)
               ▼
┌─────────────────────────────────────────────────┐
│ TOOLS NODE                                       │
│                                                  │
│ Executes both tool calls, returns results:       │
│ - AAPL: $185.42, +1.2% today                    │
│ - P/E: 28.5, Revenue Growth: 8%, ...            │
└──────────────┬──────────────────────────────────┘
               │ (edge: tools → agent)
               ▼
┌─────────────────────────────────────────────────┐
│ AGENT NODE (second pass)                         │
│                                                  │
│ LLM sees tool results in message history.        │
│ Thinks: "I have enough info to answer."          │
│                                                  │
│ Output: "Based on current data, AAPL is trading  │
│ at a P/E of 28.5 with 8% revenue growth..."     │
│ (no tool_calls → final answer)                   │
└──────────────┬──────────────────────────────────┘
               │ (conditional edge: no tool_calls → END)
               ▼
             END
```

### Key Insight: Messages Are the State

In ai-genai-cam, your state has many typed fields (`CAMStateKey.PLAN`, `CAMStateKey.GENERATED_CONTENT`, etc.).

In a ReAct agent, the primary state is **the message list**. Tool calls and results are messages.
The LLM sees the full conversation history (user messages + its own messages + tool results)
and decides what to do next based on that context.

```python
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
```

This is simpler than your CAMState — but the complexity moves from **state schema design**
to **prompt engineering and tool design**.

---

## What Makes This "Deep"

The ReAct loop above is the simplest form. What makes it a "deep agent" (from the Deep Agents PDF):

1. **Planning** — Before jumping to tools, the agent can create an explicit plan
2. **Context offload** — Write intermediate findings to state/files, don't rely solely on message history
3. **Sub-agents** — Delegate specialized research to focused sub-agents (Pillar 3)
4. **Careful prompting** — The system prompt shapes how the agent reasons, plans, and responds

We'll add these in later pillars. For now, the goal is to **experience the loop**.

---

## Implementation Steps

### Step 1: Project Scaffold

```
agentic-stock-adviser/
├── pyproject.toml
├── .env                    # OPENAI_API_KEY, OPENAI_API_BASE, etc.
├── src/
│   └── stock_adviser/
│       ├── __init__.py
│       ├── agent.py        # The ReAct agent graph
│       ├── state.py        # State definition
│       ├── llm.py          # OpenAI setup
│       └── tools/
│           ├── __init__.py
│           └── price.py    # First tool: get_stock_price
├── tests/
│   └── test_agent.py
└── docs/                   # Already exists
```

### Step 2: OpenAI Setup

```python
# llm.py — mirrors your ai-genai-cam pattern but simplified
from langchain_openai import ChatOpenAI

def get_llm(model: str = "gpt-4o") -> ChatOpenAI:
    return ChatOpenAI(
        model=model,
        temperature=0,
        # Reads OPENAI_API_KEY from env
    )
```

### Step 3: Your First Tool

```python
# tools/price.py
from langchain_core.tools import tool

@tool
def get_stock_price(symbol: str) -> dict:
    """Get the current stock price, daily change, and market cap for a ticker.

    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT', 'NVDA')
    """
    import yfinance as yf
    ticker = yf.Ticker(symbol)
    info = ticker.info
    return {
        "symbol": symbol,
        "price": info.get("currentPrice"),
        "change_percent": info.get("regularMarketChangePercent"),
        "market_cap": info.get("marketCap"),
        "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
        "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
    }
```

**Note on `@tool` vs your NodeABC pattern:** In ai-genai-cam, your nodes are classes with
`__call__`, `check_required_inputs`, and `process`. The `@tool` decorator is simpler — it's
a single function that the LLM can call. The agent loop handles orchestration, not the tool.

### Step 4: The Agent Graph

```python
# agent.py
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from stock_adviser.state import AgentState
from stock_adviser.llm import get_llm
from stock_adviser.tools.price import get_stock_price

tools = [get_stock_price]
llm = get_llm().bind_tools(tools)

def agent_node(state: AgentState):
    """The LLM decides what to do next."""
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

def should_continue(state: AgentState):
    """Route: if LLM made tool calls → tools node; otherwise → end."""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END

# Build the graph
builder = StateGraph(AgentState)
builder.add_node("agent", agent_node)
builder.add_node("tools", ToolNode(tools))
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
builder.add_edge("tools", "agent")

graph = builder.compile()
```

**What's new here vs. ai-genai-cam:**
- `bind_tools(tools)` — tells the LLM what tools are available (function calling)
- `ToolNode` — prebuilt node that executes tool calls from LLM output
- The conditional edge checks `tool_calls` — this is the LLM-controlled routing
- No explicit node-to-node edges beyond the loop — the LLM decides flow

### Step 5: Add a Checkpointer (Conversation Persistence)

```python
from langgraph.checkpoint.memory import MemorySaver

# In-memory for dev (swap to PostgresSaver or SQLiteSaver later)
memory = MemorySaver()
graph = builder.compile(checkpointer=memory)

# Now you can have multi-turn conversations:
config = {"configurable": {"thread_id": "session-1"}}

result = graph.invoke({"messages": [("user", "What's AAPL trading at?")]}, config)
# Agent calls get_stock_price, returns answer

result = graph.invoke({"messages": [("user", "How does that compare to its 52-week high?")]}, config)
# Agent sees previous context, answers from memory — no tool call needed!
```

**This is new for you:** In ai-genai-cam, each `agent.generate()` call is independent.
With a checkpointer, the agent maintains conversation state across invocations.

### Step 6: Add a System Prompt

```python
from langchain_core.messages import SystemMessage

SYSTEM_PROMPT = """You are a stock analysis assistant. You help users research stocks
and make informed investment decisions.

You have access to tools for fetching real-time stock data. Use them when the user
asks about specific stocks. Always ground your analysis in actual data.

Important:
- You are NOT a financial advisor. Always note that your analysis is for informational purposes only.
- If you don't have enough data, say so. Don't speculate without evidence.
- When presenting numbers, cite the source (e.g., "according to current market data").
"""

def agent_node(state: AgentState):
    messages = state["messages"]
    # Prepend system prompt if not already present
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    response = llm.invoke(messages)
    return {"messages": [response]}
```

---

## Exercises to Cement Understanding

1. **Add a second tool** (`get_fundamentals`) and observe how the LLM decides between them
2. **Ask a multi-step question** ("Compare AAPL and MSFT") and watch the agent call tools for both
3. **Ask a follow-up** that requires conversation context ("Which one has better growth?")
4. **Ask something the tools can't answer** ("What's the meaning of life?") — observe how the agent handles it
5. **Deliberately break a tool** (raise an exception) and see how the agent recovers

---

## Key Learning Checkpoints

Before moving to Pillar 2:

- [ ] You understand why the ReAct loop is fundamentally different from your fixed-flow graphs
- [ ] You can explain how `bind_tools` + `ToolNode` + conditional edge create the agent loop
- [ ] You've experienced multi-turn conversation with checkpointer
- [ ] You've seen the LLM make autonomous decisions about which tools to call
- [ ] You understand that tool docstrings are critical (try changing them and observe behavior)
- [ ] You've thought about the trade-offs: the LLM can make bad tool choices, call unnecessary tools, or fail to use tools when it should

---

## Patterns You'll Recognize from ai-genai-cam

| ai-genai-cam Pattern | Stock Adviser Equivalent |
|---------------------|-------------------------|
| `EnvManager` for config | `.env` + `get_llm()` function (simpler for now) |
| `NodeABC.__call__()` | `@tool` decorated functions |
| `add_messages` reducer | Same — `Annotated[list, add_messages]` |
| LangFuse tracing | LangSmith tracing (Pillar 7) |
| `save_conversation_to_db()` | LangGraph checkpointer handles this natively |
| Custom `route_after_*()` | `should_continue()` based on `tool_calls` presence |

---

## Next Step

Once you have the ReAct agent working with 1-2 tools and conversation persistence,
proceed to **docs/02-PILLAR-2-TOOLS-MCP.md** (Tools & MCP).
