# Streaming Event Pipeline

Applies when working in: `src/stock_adviser/streaming.py`, `src/stock_adviser/events/`, `src/stock_adviser/api/routes/stream.py`

## Two-layer architecture

There are two distinct event systems that must not be confused:

**Layer 1 — Internal (LangGraph-facing)**
`streaming.py` iterates the LangGraph async stream and yields `StreamEvent` typed variants:
- `TokenEvent` — one LLM text chunk
- `ToolStartEvent` — LLM has emitted a tool call request (includes status string from tool metadata)
- `ToolResultEvent` — a tool has returned its output
- `StateEvent` — full message history snapshot (used to update session, not sent to frontend)

**Layer 2 — Wire format (frontend-facing)**
`events/types.py` defines `SSEEvent` subclasses serialised to JSON over SSE:
- `Token`, `ToolStart`, `ToolResult`, `Done`, `Error` — chat flow events
- `StockOpened`, `ChartUpdate`, `TableUpdate`, `ReportUpdate` — dashboard data events

## How the layers connect

`api/routes/stream.py::_event_generator` is the single place that converts Layer 1 → Layer 2:

```
TokenEvent      → Token.to_sse()
ToolStartEvent  → ToolStart.to_sse()
ToolResultEvent → ToolResult.to_sse() + route_tool_result() → dashboard events
StateEvent      → sessions.update() (not sent to frontend)
```

`events/router.py::route_tool_result` handles the dashboard events:
- Looks up the tool name in `_HANDLERS`
- Returns a list of `SSEEvent` objects
- Auto-prepends `StockOpened` for data tools (so the frontend always has a tab open before receiving data)
- `search_ticker` is exempt — it emits its own `StockOpened` with the real company name

## Adding a new tool

1. Add a handler function `_handle_<toolname>(data: dict) -> list[SSEEvent]` in `events/router.py`
2. Register it in `_HANDLERS`
3. If the tool returns stock data, return a `ChartUpdate`, `TableUpdate`, or `ReportUpdate` — the `StockOpened` auto-prepend will handle tab creation
4. Add the tool to `src/stock_adviser/tools/` with a `@tool` decorator and `.metadata["status"]` for the UI status message

## Adding a new dashboard event type

1. Add a new `SSEEvent` subclass in `events/types.py` with a unique `event_type` string
2. Override `to_sse()` only if the default serialisation (all non-`event_type` fields) doesn't fit
3. Emit it from the appropriate handler in `events/router.py`
4. Handle the new `type` in `frontend/src/stream/useSSE.ts` to update the Zustand store

## Tool status messages

Each tool controls its own UI status message via `metadata["status"]` on the `@tool` decorator. `streaming.py` builds a lookup dict from this at import time. The fallback is `"Working on it..."`.
