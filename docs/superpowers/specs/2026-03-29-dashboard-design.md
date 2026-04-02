# Dashboard Design Spec

## Overview

A web-based dashboard for the stock adviser agent. Users interact via a chat panel (the sole entry point); the agent researches stocks and pushes structured data to dashboard panes in real time via SSE.

**Stack**: FastAPI (backend, SSE) + React (frontend) + assistant-ui (chat widget)

---

## User Experience

### Entry Flow

1. User opens the dashboard. Main area shows a placeholder ("Ask the agent about any stock"). Chat panel is open on the right with a welcome message.
2. User types "Research AAPL" in the chat.
3. Agent calls tools. Each tool result emits a typed SSE event. Frontend routes events to the correct pane.
4. An "AAPL" stock tab appears. Sub-tabs (Chart / Fundamentals / Report) populate as data arrives.

### Layout

```
+---------------------------------------------+------------------+
|  [AAPL x] [MSFT x] [+]                      |  Agent     [<<]  |
|  ------------------------------------------ |                  |
|  [Chart] [Fundamentals] [Report]             |  (chat messages) |
|                                              |                  |
|  +----------------------------------------+ |                  |
|  |                                        | |                  |
|  |  (full-width content for active tab)   | |  [input box]     |
|  |                                        | |                  |
|  +----------------------------------------+ |                  |
+---------------------------------------------+------------------+
```

- **Stock tabs**: Top bar. Close button on each. User controls their workspace.
- **Sub-tabs**: Chart / Fundamentals / Report within each stock tab.
- **Chat panel**: Right side, collapsible (VS Code style). `<<` retracts, `>>` expands. Open by default.
- **Empty state**: Prompt-first. Placeholder in main area, chat panel has the welcome message.

### Sub-tab Content

| Sub-tab        | Content                              | Data source           |
|---------------|--------------------------------------|-----------------------|
| Chart         | Price history line chart              | `chart_update` SSE    |
| Fundamentals  | Metrics table (P/E, EPS, margins...) | `table_update` SSE    |
| Report        | Markdown-rendered analysis           | `report_update` SSE   |

Report is free-form markdown written by the agent. No rating badge or structured header for now.

---

## Architecture

### Data Flow

```
User (chat input)
  --> Frontend (assistant-ui) sends message via POST /chat
  --> FastAPI endpoint invokes LangGraph agent
  --> Agent calls tools, LLM streams response
  --> FastAPI emits SSE events on GET /stream/{session_id}
  --> Frontend routes events to chat panel or dashboard panes
```

### SSE Event Types

All events are JSON with a `type` field. The frontend uses `type` to route to the correct handler.

```
type: "token"          -- LLM text chunk for chat panel
type: "tool_start"     -- Tool invocation started (status message for chat)
type: "tool_result"    -- Tool finished (status message for chat)
type: "chart_update"   -- Price data payload for Chart sub-tab
type: "table_update"   -- Fundamentals payload for Fundamentals sub-tab
type: "report_update"  -- Markdown content for Report sub-tab
type: "stock_opened"   -- Signal to create a new stock tab
```

Example payloads:

```json
{"type": "stock_opened", "data": {"symbol": "AAPL", "name": "Apple Inc."}}
{"type": "token", "data": {"content": "Let me look up "}}
{"type": "tool_start", "data": {"tool": "get_stock_price", "status": "Fetching the latest price..."}}
{"type": "chart_update", "data": {"symbol": "AAPL", "prices": [...], "period": "1y"}}
{"type": "table_update", "data": {"symbol": "AAPL", "metrics": {"pe_ratio": 31.5, ...}}}
{"type": "report_update", "data": {"symbol": "AAPL", "markdown": "## Analysis\n..."}}
```

### API Coordination

The frontend opens two connections per session:

1. **`GET /stream/{session_id}`** — Opened once on page load. Long-lived SSE connection. All events (chat tokens, tool status, dashboard updates) flow through this single stream.
2. **`POST /chat`** — Fire-and-forget per user message. Accepts `{session_id, message}`. The backend appends the message to conversation history and triggers the agent. Results arrive via the SSE stream, not the POST response.

This avoids request-response coupling. The POST returns immediately (202 Accepted). The frontend doesn't need to correlate POST responses with SSE events — it just reacts to whatever arrives on the stream.

### Session Model

Each browser tab gets a `session_id` (generated client-side, UUID). The backend holds conversation state per session in memory. For now, no persistence across restarts. LangGraph checkpointing can be added later by mapping `session_id` to `thread_id`.

---

## Code Organisation

### Backend (Python)

The backend lives under `src/stock_adviser/` alongside the existing agent code. New modules are grouped by responsibility.

```
src/stock_adviser/
    # --- Existing (agent core) ---
    graph.py              # LangGraph agent
    llm.py                # LLM factory
    models.py             # Pydantic models (tool inputs/outputs)
    prompts.py            # System prompt
    state.py              # AgentState
    streaming.py          # Stream event classification (reused by API)
    __main__.py           # Terminal REPL (kept as alternative interface)
    tools/
        __init__.py
        search.py
        price.py
        fundamentals.py

    # --- New (API layer) ---
    api/
        __init__.py
        app.py            # FastAPI app factory, CORS, lifespan
        routes/
            __init__.py
            chat.py       # POST /chat -- accept user message, trigger agent
            stream.py     # GET /stream/{session_id} -- SSE endpoint
            health.py     # GET /health
        middleware/
            __init__.py
            errors.py     # Global exception handlers
        dependencies.py   # Shared FastAPI dependencies (session lookup, etc.)

    # --- New (SSE event layer) ---
    events/
        __init__.py
        types.py          # SSE event dataclasses (ChartUpdate, TableUpdate, etc.)
        emitter.py        # Converts streaming.StreamEvent -> SSE event JSON
        router.py         # Maps tool results to dashboard event types
```

**Key design decisions**:

- `streaming.py` (existing) stays unchanged. It yields typed `StreamEvent` objects from the LangGraph stream. The new `events/emitter.py` consumes these and converts them to SSE-formatted JSON. This keeps the agent core completely decoupled from the transport layer.
- `events/router.py` decides which tool result becomes which dashboard event. When `get_stock_price` returns data, the router emits a `chart_update`. When `get_fundamentals` returns, it emits a `table_update`. This mapping is centralised and easy to extend as new tools are added.
- `api/routes/` is split by endpoint group, not lumped into one file. Each route module is small and focused.
- `api/app.py` is a factory function (`create_app()`) so tests can create isolated app instances.

### Frontend (React/TypeScript)

The frontend is a separate directory at the repo root. It is a standalone app with its own `package.json`.

```
frontend/
    package.json
    tsconfig.json
    vite.config.ts
    public/
    src/
        main.tsx                  # React entry point
        App.tsx                   # Top-level layout (dashboard + chat)

        # --- Chat panel ---
        chat/
            ChatPanel.tsx         # The collapsible right panel container
            ChatMessages.tsx      # Message list rendering
            ChatInput.tsx         # Input box + send button
            useChat.ts            # Hook: manages chat state, sends messages

        # --- Dashboard (main area) ---
        dashboard/
            Dashboard.tsx         # Stock tabs + sub-tab routing
            StockTab.tsx          # Single stock tab content (switches sub-tabs)
            EmptyState.tsx        # Placeholder shown when no stocks open

        # --- Sub-tab panes ---
        panes/
            ChartPane.tsx         # Price chart (wraps a charting library)
            FundamentalsPane.tsx  # Metrics table
            ReportPane.tsx        # Markdown renderer

        # --- SSE and state ---
        stream/
            useSSE.ts             # Hook: connects to SSE endpoint, parses events
            eventRouter.ts        # Routes SSE events to the correct state slice

        # --- Shared state ---
        store/
            index.ts              # Zustand store (or React context)
            types.ts              # TypeScript types for dashboard state
            slices/
                chatSlice.ts      # Chat messages state
                stocksSlice.ts    # Open stocks, their data, active tab
```

**Key design decisions**:

- **Flat feature folders** (`chat/`, `dashboard/`, `panes/`, `stream/`, `store/`). Each folder owns its components, hooks, and logic. No deep nesting.
- **`stream/useSSE.ts`** is the single connection point to the backend. It opens one `EventSource`, parses JSON, and dispatches to the store via `eventRouter.ts`. Components never touch SSE directly.
- **`store/`** uses Zustand (lightweight, no boilerplate). Slices keep chat state and stock data separate. The event router writes to the correct slice based on event type.
- **Panes are isolated**. `ChartPane` receives data as props — it doesn't know about SSE or the store. This makes panes testable and reusable.
- **No bidirectional sync needed yet**. Chat sends messages via POST. Dashboard reads from store (populated by SSE). Data flows one direction: chat -> backend -> SSE -> store -> panes.

---

## Extensibility Points

The architecture is designed so that future features slot into existing seams without restructuring.

| Future feature                | Where it plugs in                                                    |
|------------------------------|----------------------------------------------------------------------|
| New tool (e.g. sentiment)    | Add tool in `tools/`, add event type in `events/types.py`, add routing rule in `events/router.py`, add pane in `panes/` |
| New sub-tab                  | Add pane component in `panes/`, register in `StockTab.tsx` sub-tab list |
| Rating badge on report       | Add structured header to `ReportPane.tsx`, parse from `report_update` payload |
| Quick picks / dashboard clicks | Add handler in `eventRouter.ts` that injects a chat message into `chatSlice` |
| Session persistence          | Swap in-memory session store for Redis/DB in `api/dependencies.py`   |
| LangGraph checkpointing      | Add checkpointer to `graph.compile()`, thread_id from session_id     |
| Multiple agents              | Each agent gets its own graph, `events/router.py` tags events by source |
| WebSocket (replace SSE)      | Swap `stream/useSSE.ts` for `useWebSocket.ts`, backend adds WS route |
| Authentication               | Add auth middleware in `api/middleware/`, guard routes               |

---

## What This Spec Does NOT Cover

- Authentication / authorisation (no users yet)
- Session persistence across restarts (in-memory for now)
- Charting library choice (decided during implementation)
- CSS framework / design system (decided during implementation)
- Deployment / containerisation (later pillar)
- Rating badge / structured report header (future feature)
- Quick picks or dashboard-initiated actions (future feature)

---

## Dependencies (New)

### Backend
- `fastapi` — API framework
- `uvicorn` — ASGI server
- `sse-starlette` — SSE support for FastAPI

### Frontend
- `react` + `react-dom` — UI framework
- `@assistant-ui/react` — Chat widget (AssistantModal or custom)
- `zustand` — State management
- `react-markdown` — Report rendering
- A charting library (TBD — recharts, lightweight-charts, or similar)
- `vite` — Build tool
