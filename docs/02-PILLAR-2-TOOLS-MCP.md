# Pillar 2: Tools & MCP — Connecting to the Real World

> **Goal:** Build a comprehensive library of stock analysis tools, and learn to expose them via MCP.
> **Patterns:** Tool Use (5), MCP (10)
> **Reference:** deep_research_from_scratch Notebook 3, Agentic Patterns Ch. 5, 10

---

## Concepts to Master

### 2.1 Tool Design Principles

- **Single responsibility** — Each tool does one thing well
- **Clear contracts** — Typed inputs, typed outputs, descriptive docstrings
- **Graceful failure** — Return error info, don't crash the agent
- **Appropriate granularity** — Not too broad (the LLM can't reason about a wall of data), not too narrow (death by 100 tool calls)

### 2.2 The Tool Library for Stock Analysis

| Tool | Purpose | Data Source | Priority |
|------|---------|-------------|----------|
| `get_stock_price` | Current price, change, market cap | yfinance | P0 |
| `get_fundamentals` | P/E, EPS, margins, revenue growth, debt | yfinance | P0 |
| `get_technical_indicators` | RSI, MACD, SMA, Bollinger Bands | yfinance + pandas | P0 |
| `get_analyst_ratings` | Price targets, buy/hold/sell consensus | yfinance | P1 |
| `get_insider_trades` | Recent insider buys/sells | OpenInsider/Investegate | P1 |
| `get_news_sentiment` | Recent news with sentiment scores | News API / Google News | P1 |
| `get_sector_performance` | Sector vs market performance | yfinance sector ETFs | P1 |
| `get_macro_indicators` | Interest rates, inflation, GDP | FRED API | P2 |
| `get_earnings_history` | Past earnings beats/misses | yfinance | P2 |
| `get_peer_comparison` | Compare against sector peers | yfinance | P2 |
| `create_price_chart` | Generate visual price chart | matplotlib/plotly | P2 |
| `calculate_fair_value` | DCF or comparable valuation | computed | P3 |

### 2.3 MCP (Model Context Protocol)

MCP wraps tools into a **standardized server** that any MCP-compatible client can discover and use:

```
┌──────────┐     MCP Protocol     ┌──────────────┐
│ LangGraph │ ◄──────────────────► │ Stock Data   │
│  Agent    │   (tool discovery,   │ MCP Server   │
│           │    tool calls,       │              │
│           │    results)          │ - price tool │
│           │                      │ - fundamentals│
└──────────┘                      │ - technicals  │
                                  └──────────────┘
```

**Why MCP matters for this project:**
- Your tools become reusable across different agents and frameworks
- You can run tools as separate processes (isolation, scaling)
- Other people/agents could connect to your stock data server
- It's the direction the industry is going (see Agentic Patterns Ch. 10)

### 2.4 Native Tools vs. MCP

Start with **native tools** (Python functions with `@tool`). Once they work, wrap them in an MCP server. This gives you both:
- Fast iteration during development (native)
- Standardized interface for production (MCP)

---

## Implementation Steps

### Step 1: Port Tools from stock-selector
Your existing scrapers are a goldmine. Refactor them into clean tool functions.

### Step 2: Add Error Handling & Rate Limiting
Tools that hit external APIs need: retry logic, rate limiting, caching, timeout handling.

### Step 3: Build Your First MCP Server
Take 2-3 tools and expose them via an MCP server using `mcp` Python package.

### Step 4: Connect LangGraph to MCP
Use `langchain_mcp_adapters` to have your LangGraph agent discover and use MCP tools.

---

## Key Learning Checkpoints

- [ ] Can you define a tool that the LLM consistently uses correctly?
- [ ] How do you handle tool errors without crashing the agent?
- [ ] What's the difference between native tools and MCP tools from the agent's perspective?
- [ ] Can you run an MCP server and connect to it from your agent?

---

## Next Step

Proceed to **docs/03-PILLAR-3-MULTI-AGENT.md** (Multi-Agent Architecture).
