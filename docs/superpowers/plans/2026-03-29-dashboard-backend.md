# Dashboard Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the FastAPI backend that serves SSE events from the LangGraph agent to a browser-based dashboard.

**Architecture:** The existing `streaming.py` yields typed events from LangGraph. A new `events/` layer converts tool results into dashboard-specific SSE events (chart_update, table_update, report_update). A new `api/` layer exposes two endpoints: POST /chat (fire-and-forget message submission) and GET /stream/{session_id} (long-lived SSE connection). Sessions are in-memory.

**Tech Stack:** FastAPI, uvicorn, sse-starlette, existing LangGraph agent + streaming module

**Spec:** `docs/superpowers/specs/2026-03-29-dashboard-design.md`

---

## File Map

```
src/stock_adviser/
    # Modified
    streaming.py          # Add ToolResultData to carry parsed tool output

    # New: events layer
    events/
        __init__.py
        types.py          # SSE event dataclasses (ChartUpdate, TableUpdate, etc.)
        router.py         # Maps tool name + result data -> dashboard SSE events

    # New: API layer
    api/
        __init__.py
        app.py            # FastAPI app factory (create_app), CORS, lifespan
        session.py        # In-memory session store (conversation history per session_id)
        routes/
            __init__.py
            health.py     # GET /health
            chat.py       # POST /chat — accept message, trigger agent in background
            stream.py     # GET /stream/{session_id} — SSE endpoint

tests/
    test_events.py        # Tests for events/types.py and events/router.py
    test_api.py           # Tests for API endpoints using FastAPI TestClient
    test_session.py       # Tests for session store

scripts/
    e2e_api_test.py       # E2E test: start server, send messages, verify SSE events
```

---

### Task 1: Add Backend Dependencies

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add fastapi, uvicorn, sse-starlette, httpx to pyproject.toml**

```bash
cd /home/zz/Work/github_personal/agentic-stock-adviser
poetry add fastapi uvicorn sse-starlette
poetry add --group dev httpx
```

httpx is needed for FastAPI's TestClient.

- [ ] **Step 2: Verify installation**

Run: `poetry run python -c "import fastapi; import sse_starlette; import uvicorn; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml poetry.lock
git commit -m "chore: add fastapi, uvicorn, sse-starlette dependencies"
```

---

### Task 2: SSE Event Types

**Files:**
- Create: `src/stock_adviser/events/__init__.py`
- Create: `src/stock_adviser/events/types.py`
- Test: `tests/test_events.py`

- [ ] **Step 1: Write failing tests for SSE event types**

Create `tests/test_events.py`:

```python
"""Tests for SSE event types and serialisation."""

import json

from stock_adviser.events.types import (
    ChartUpdate,
    ReportUpdate,
    SSEEvent,
    StockOpened,
    TableUpdate,
    Token,
    ToolStart,
    ToolResult,
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `poetry run pytest tests/test_events.py -v`
Expected: FAIL (ModuleNotFoundError: No module named 'stock_adviser.events')

- [ ] **Step 3: Implement SSE event types**

Create `src/stock_adviser/events/__init__.py`:

```python
```

Create `src/stock_adviser/events/types.py`:

```python
"""Typed SSE events for the dashboard.

Each event knows how to serialise itself to the SSE wire format:
{"event": "message", "data": '{"type": "...", "data": {...}}'}
"""

import json
from dataclasses import asdict, dataclass, fields


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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `poetry run pytest tests/test_events.py -v`
Expected: All 8 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/stock_adviser/events/ tests/test_events.py
git commit -m "feat: add SSE event types with serialisation"
```

---

### Task 3: Event Router (Tool Result -> Dashboard Events)

**Files:**
- Create: `src/stock_adviser/events/router.py`
- Modify: `src/stock_adviser/streaming.py` (add tool result content to ToolResultEvent)
- Test: `tests/test_events.py` (append new tests)

- [ ] **Step 1: Write failing tests for the event router**

Append to `tests/test_events.py`:

```python
from stock_adviser.events.router import route_tool_result
from stock_adviser.events.types import StockOpened


class TestEventRouter:
    def test_routes_get_stock_price_to_chart_update(self):
        tool_content = json.dumps({
            "symbol": "AAPL",
            "price": 248.80,
            "change_percent": -1.62,
            "market_cap": 3800000000000,
            "fifty_two_week_high": 260.0,
            "fifty_two_week_low": 164.0,
            "fifty_day_average": 240.0,
            "two_hundred_day_average": 220.0,
        })
        events = route_tool_result("get_stock_price", tool_content)
        assert len(events) == 1
        assert isinstance(events[0], ChartUpdate)
        assert events[0].symbol == "AAPL"

    def test_routes_get_fundamentals_to_table_update(self):
        tool_content = json.dumps({
            "symbol": "AAPL",
            "pe_ratio": 31.5,
            "forward_pe": 28.0,
            "eps": 7.91,
            "revenue_growth": 0.157,
            "profit_margin": 0.27,
            "debt_to_equity": 1.5,
            "return_on_equity": 0.45,
            "dividend_yield": 0.005,
        })
        events = route_tool_result("get_fundamentals", tool_content)
        assert len(events) == 1
        assert isinstance(events[0], TableUpdate)
        assert events[0].symbol == "AAPL"
        assert events[0].metrics["pe_ratio"] == 31.5

    def test_routes_search_ticker_to_stock_opened(self):
        tool_content = json.dumps({"query": "Apple", "matches": [{"symbol": "AAPL", "name": "Apple Inc.", "exchange": "NMS"}]})
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `poetry run pytest tests/test_events.py::TestEventRouter -v`
Expected: FAIL (ImportError: cannot import name 'route_tool_result')

- [ ] **Step 3: Implement the event router**

Create `src/stock_adviser/events/router.py`:

```python
"""Route tool results to dashboard SSE events.

Maps each tool's output to the appropriate dashboard event type.
New tools are added by adding a handler function and registering it in _HANDLERS.
"""

import json

from stock_adviser.events.types import ChartUpdate, SSEEvent, StockOpened, TableUpdate


def _handle_search_ticker(data: dict) -> list[SSEEvent]:
    matches = data.get("matches", [])
    if not matches:
        return []
    first = matches[0]
    return [StockOpened(symbol=first["symbol"], name=first.get("name", ""))]


def _handle_stock_price(data: dict) -> list[SSEEvent]:
    return [
        ChartUpdate(
            symbol=data["symbol"],
            prices=[data.get("price", 0.0)],
            period="latest",
        )
    ]


def _handle_fundamentals(data: dict) -> list[SSEEvent]:
    symbol = data.pop("symbol")
    return [TableUpdate(symbol=symbol, metrics=data)]


# Register handlers by tool name. To add a new tool, write a handler and add it here.
_HANDLERS: dict[str, callable] = {
    "search_ticker": _handle_search_ticker,
    "get_stock_price": _handle_stock_price,
    "get_fundamentals": _handle_fundamentals,
}


def route_tool_result(tool_name: str, tool_content: str) -> list[SSEEvent]:
    """Convert a tool's string output to dashboard SSE events.

    Returns an empty list if:
    - The tool has no registered handler
    - The content contains an error
    - The content is not valid JSON
    """
    handler = _HANDLERS.get(tool_name)
    if not handler:
        return []

    try:
        data = json.loads(tool_content)
    except (json.JSONDecodeError, TypeError):
        return []

    if "error" in data:
        return []

    return handler(data)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `poetry run pytest tests/test_events.py -v`
Expected: All 14 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/stock_adviser/events/router.py tests/test_events.py
git commit -m "feat: add event router mapping tool results to dashboard events"
```

---

### Task 4: Enhance ToolResultEvent with Content

The existing `ToolResultEvent` in `streaming.py` carries no data. The SSE stream endpoint needs the tool name and content to route to dashboard events. We'll add these fields.

**Files:**
- Modify: `src/stock_adviser/streaming.py`
- Modify: `src/stock_adviser/__main__.py` (update to handle new fields — it just ignores them)
- Test: `tests/test_streaming.py`

- [ ] **Step 1: Write failing test for enhanced ToolResultEvent**

Create `tests/test_streaming.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `poetry run pytest tests/test_streaming.py -v`
Expected: FAIL (TypeError: ToolResultEvent() got unexpected keyword argument 'tool_name')

- [ ] **Step 3: Update ToolResultEvent in streaming.py**

In `src/stock_adviser/streaming.py`, update the `ToolResultEvent` dataclass and the stream loop:

Replace the existing `ToolResultEvent`:

```python
@dataclass
class ToolResultEvent:
    """A tool has returned its result."""

    tool_name: str = ""
    content: str = ""
```

Replace the `elif isinstance(chunk, ToolMessage):` block at the bottom of `stream_events`:

```python
            elif isinstance(chunk, ToolMessage):
                yield ToolResultEvent(tool_name=chunk.name or "", content=chunk.content or "")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `poetry run pytest tests/test_streaming.py tests/test_graph.py -v`
Expected: All PASS

- [ ] **Step 5: Verify __main__.py still works (it ignores the new fields)**

Run: `poetry run pytest tests/ -v --tb=short -q`
Expected: All existing tests still PASS

- [ ] **Step 6: Commit**

```bash
git add src/stock_adviser/streaming.py tests/test_streaming.py
git commit -m "feat: add tool_name and content to ToolResultEvent for SSE routing"
```

---

### Task 5: Session Store

**Files:**
- Create: `src/stock_adviser/api/__init__.py`
- Create: `src/stock_adviser/api/session.py`
- Test: `tests/test_session.py`

- [ ] **Step 1: Write failing tests for session store**

Create `tests/test_session.py`:

```python
"""Tests for in-memory session store."""

from langchain_core.messages import HumanMessage

from stock_adviser.api.session import SessionStore


class TestSessionStore:
    def test_create_new_session(self):
        store = SessionStore()
        session = store.get_or_create("abc-123")
        assert session == []

    def test_get_existing_session(self):
        store = SessionStore()
        store.get_or_create("abc-123")
        msg = HumanMessage(content="hello")
        store.append("abc-123", msg)
        session = store.get_or_create("abc-123")
        assert len(session) == 1
        assert session[0].content == "hello"

    def test_append_message(self):
        store = SessionStore()
        store.get_or_create("abc-123")
        store.append("abc-123", HumanMessage(content="first"))
        store.append("abc-123", HumanMessage(content="second"))
        session = store.get_or_create("abc-123")
        assert len(session) == 2

    def test_append_to_nonexistent_session_creates_it(self):
        store = SessionStore()
        store.append("new-id", HumanMessage(content="hello"))
        session = store.get_or_create("new-id")
        assert len(session) == 1

    def test_update_replaces_messages(self):
        store = SessionStore()
        store.get_or_create("abc-123")
        new_messages = [HumanMessage(content="updated")]
        store.update("abc-123", new_messages)
        session = store.get_or_create("abc-123")
        assert len(session) == 1
        assert session[0].content == "updated"

    def test_sessions_are_isolated(self):
        store = SessionStore()
        store.append("session-1", HumanMessage(content="one"))
        store.append("session-2", HumanMessage(content="two"))
        assert len(store.get_or_create("session-1")) == 1
        assert len(store.get_or_create("session-2")) == 1
        assert store.get_or_create("session-1")[0].content == "one"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `poetry run pytest tests/test_session.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Implement session store**

Create `src/stock_adviser/api/__init__.py`:

```python
```

Create `src/stock_adviser/api/session.py`:

```python
"""In-memory session store for conversation history.

Each session_id maps to a list of LangChain messages.
No persistence across restarts — designed to be swapped for
Redis/DB later via the same interface.
"""

from langchain_core.messages import BaseMessage


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, list[BaseMessage]] = {}

    def get_or_create(self, session_id: str) -> list[BaseMessage]:
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        return self._sessions[session_id]

    def append(self, session_id: str, message: BaseMessage) -> None:
        self.get_or_create(session_id)
        self._sessions[session_id].append(message)

    def update(self, session_id: str, messages: list[BaseMessage]) -> None:
        self._sessions[session_id] = messages
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `poetry run pytest tests/test_session.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/stock_adviser/api/ tests/test_session.py
git commit -m "feat: add in-memory session store for conversation history"
```

---

### Task 6: Health Route

**Files:**
- Create: `src/stock_adviser/api/routes/__init__.py`
- Create: `src/stock_adviser/api/routes/health.py`
- Create: `src/stock_adviser/api/app.py`
- Test: `tests/test_api.py`

- [ ] **Step 1: Write failing test for health endpoint**

Create `tests/test_api.py`:

```python
"""Tests for FastAPI endpoints."""

from fastapi.testclient import TestClient

from stock_adviser.api.app import create_app


class TestHealthEndpoint:
    def test_health_returns_ok(self):
        app = create_app()
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `poetry run pytest tests/test_api.py::TestHealthEndpoint -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Implement health route and app factory**

Create `src/stock_adviser/api/routes/__init__.py`:

```python
```

Create `src/stock_adviser/api/routes/health.py`:

```python
"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}
```

Create `src/stock_adviser/api/app.py`:

```python
"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from stock_adviser.api.routes.health import router as health_router
from stock_adviser.api.session import SessionStore


def create_app() -> FastAPI:
    app = FastAPI(title="Stock Adviser API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Shared session store — attached to app state so routes can access it
    app.state.sessions = SessionStore()

    app.include_router(health_router)

    return app
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `poetry run pytest tests/test_api.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/stock_adviser/api/ tests/test_api.py
git commit -m "feat: add FastAPI app factory with health endpoint"
```

---

### Task 7: POST /chat Endpoint

**Files:**
- Create: `src/stock_adviser/api/routes/chat.py`
- Modify: `src/stock_adviser/api/app.py` (register chat router)
- Test: `tests/test_api.py` (append)

- [ ] **Step 1: Write failing tests for chat endpoint**

Append to `tests/test_api.py`:

```python
class TestChatEndpoint:
    def test_chat_returns_202(self):
        app = create_app()
        client = TestClient(app)
        response = client.post("/chat", json={"session_id": "test-1", "message": "Hello"})
        assert response.status_code == 202

    def test_chat_rejects_empty_message(self):
        app = create_app()
        client = TestClient(app)
        response = client.post("/chat", json={"session_id": "test-1", "message": ""})
        assert response.status_code == 422

    def test_chat_rejects_missing_session_id(self):
        app = create_app()
        client = TestClient(app)
        response = client.post("/chat", json={"message": "Hello"})
        assert response.status_code == 422

    def test_chat_appends_message_to_session(self):
        app = create_app()
        client = TestClient(app)
        client.post("/chat", json={"session_id": "test-1", "message": "Hello"})
        session = app.state.sessions.get_or_create("test-1")
        assert len(session) >= 1
        assert session[0].content == "Hello"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `poetry run pytest tests/test_api.py::TestChatEndpoint -v`
Expected: FAIL

- [ ] **Step 3: Implement chat endpoint**

Create `src/stock_adviser/api/routes/chat.py`:

```python
"""POST /chat — accept a user message and trigger the agent."""

import asyncio

from fastapi import APIRouter, Request
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, field_validator

from stock_adviser.api.session import SessionStore
from stock_adviser.streaming import StateEvent, stream_events

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str
    message: str

    @field_validator("message")
    @classmethod
    def message_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("message must not be empty")
        return v.strip()


def _run_agent(sessions: SessionStore, session_id: str) -> None:
    """Run the agent synchronously and update session with final state."""
    messages = sessions.get_or_create(session_id)
    for event in stream_events(messages):
        if isinstance(event, StateEvent):
            sessions.update(session_id, event.messages)


@router.post("/chat", status_code=202)
async def chat(body: ChatRequest, request: Request) -> dict:
    sessions: SessionStore = request.app.state.sessions
    sessions.append(body.session_id, HumanMessage(content=body.message))

    # Run agent in background thread so POST returns immediately
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, _run_agent, sessions, body.session_id)

    return {"status": "accepted"}
```

Modify `src/stock_adviser/api/app.py` — add the chat router import and registration:

Add after the health_router import:

```python
from stock_adviser.api.routes.chat import router as chat_router
```

Add after `app.include_router(health_router)`:

```python
    app.include_router(chat_router)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `poetry run pytest tests/test_api.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/stock_adviser/api/ tests/test_api.py
git commit -m "feat: add POST /chat endpoint with session management"
```

---

### Task 8: GET /stream/{session_id} SSE Endpoint

This is the core of the dashboard backend. It opens a long-lived SSE connection that streams all events (chat tokens, tool status, dashboard updates) for a session.

**Files:**
- Create: `src/stock_adviser/api/routes/stream.py`
- Modify: `src/stock_adviser/api/app.py` (register stream router)
- Test: `tests/test_api.py` (append)

- [ ] **Step 1: Write failing test for stream endpoint**

Append to `tests/test_api.py`:

```python
class TestStreamEndpoint:
    def test_stream_returns_event_stream_content_type(self):
        app = create_app()
        client = TestClient(app)
        # Create session first
        app.state.sessions.get_or_create("test-stream")
        with client.stream("GET", "/stream/test-stream") as response:
            assert response.status_code == 200
            assert "text/event-stream" in response.headers["content-type"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `poetry run pytest tests/test_api.py::TestStreamEndpoint -v`
Expected: FAIL (404 — route not registered)

- [ ] **Step 3: Implement SSE stream endpoint**

Create `src/stock_adviser/api/routes/stream.py`:

```python
"""GET /stream/{session_id} — SSE endpoint for real-time events."""

import asyncio
import json
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from stock_adviser.api.session import SessionStore
from stock_adviser.events.router import route_tool_result
from stock_adviser.events.types import Token, ToolResult, ToolStart
from stock_adviser.streaming import (
    StateEvent,
    TokenEvent,
    ToolResultEvent,
    ToolStartEvent,
    stream_events,
)

router = APIRouter()


async def _event_generator(sessions: SessionStore, session_id: str) -> AsyncGenerator[dict, None]:
    """Watch for new messages in the session and stream agent events as SSE.

    This generator polls for new messages. When a new message appears (from POST /chat),
    it runs the agent and streams events. In production, this would use an asyncio.Event
    or queue instead of polling.
    """
    last_count = len(sessions.get_or_create(session_id))

    while True:
        messages = sessions.get_or_create(session_id)
        current_count = len(messages)

        if current_count > last_count:
            # New message arrived — run agent and stream events
            last_count = current_count

            def _stream():
                return list(stream_events(messages))

            loop = asyncio.get_event_loop()
            events = await loop.run_in_executor(None, _stream)

            for event in events:
                if isinstance(event, TokenEvent):
                    yield Token(content=event.content).to_sse()

                elif isinstance(event, ToolStartEvent):
                    yield ToolStart(tool=event.tool_name, status=event.status).to_sse()

                elif isinstance(event, ToolResultEvent):
                    yield ToolResult().to_sse()
                    # Route tool result to dashboard events
                    dashboard_events = route_tool_result(event.tool_name, event.content)
                    for de in dashboard_events:
                        yield de.to_sse()

                elif isinstance(event, StateEvent):
                    sessions.update(session_id, event.messages)
                    last_count = len(event.messages)

        await asyncio.sleep(0.1)


@router.get("/stream/{session_id}")
async def stream(session_id: str, request: Request) -> EventSourceResponse:
    sessions: SessionStore = request.app.state.sessions
    sessions.get_or_create(session_id)
    return EventSourceResponse(_event_generator(sessions, session_id))
```

Modify `src/stock_adviser/api/app.py` — add the stream router:

Add after the chat_router import:

```python
from stock_adviser.api.routes.stream import router as stream_router
```

Add after `app.include_router(chat_router)`:

```python
    app.include_router(stream_router)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `poetry run pytest tests/test_api.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/stock_adviser/api/ tests/test_api.py
git commit -m "feat: add SSE stream endpoint with event routing"
```

---

### Task 9: Server Entry Point

**Files:**
- Create: `src/stock_adviser/server.py`
- Modify: `Makefile` (add serve target)

- [ ] **Step 1: Create server entry point**

Create `src/stock_adviser/server.py`:

```python
"""Run the FastAPI server."""

import uvicorn

from stock_adviser.api.app import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("stock_adviser.server:app", host="0.0.0.0", port=8000, reload=True)
```

- [ ] **Step 2: Add Makefile target**

Add to `Makefile` before the `clean` target:

```makefile
# Run the API server
serve:
	poetry run uvicorn stock_adviser.server:app --host 0.0.0.0 --port 8000 --reload
```

- [ ] **Step 3: Verify server starts**

Run: `poetry run python -c "from stock_adviser.api.app import create_app; print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add src/stock_adviser/server.py Makefile
git commit -m "feat: add server entry point and make serve target"
```

---

### Task 10: E2E API Test Script

**Files:**
- Create: `scripts/e2e_api_test.py`

- [ ] **Step 1: Create e2e test script**

Create `scripts/e2e_api_test.py`:

```python
"""E2E test for the API — starts the server, sends messages, verifies SSE events.

Run with: poetry run python scripts/e2e_api_test.py
Requires OPENAI env vars to be set (calls the real LLM).
"""

import json
import threading
import time

import httpx
import uvicorn

from stock_adviser.api.app import create_app


def start_server(app, port: int) -> threading.Thread:
    """Start uvicorn in a background thread."""
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    time.sleep(1)  # Wait for server to start
    return thread


def test_health(base_url: str) -> None:
    print("Test: GET /health")
    r = httpx.get(f"{base_url}/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    print("  PASS")


def test_chat_and_stream(base_url: str) -> None:
    print("Test: POST /chat + GET /stream (specific price request)")
    session_id = "e2e-test-1"

    # Collect SSE events in background
    events: list[dict] = []
    stop = threading.Event()

    def collect_events():
        with httpx.stream("GET", f"{base_url}/stream/{session_id}", timeout=60) as r:
            for line in r.iter_lines():
                if stop.is_set():
                    break
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        events.append(data)
                        print(f"  SSE: {data['type']}")
                    except json.JSONDecodeError:
                        pass

    collector = threading.Thread(target=collect_events, daemon=True)
    collector.start()
    time.sleep(0.5)

    # Send a specific request that should trigger tools
    r = httpx.post(f"{base_url}/chat", json={"session_id": session_id, "message": "What is the price of AAPL?"})
    assert r.status_code == 202
    print(f"  POST /chat: {r.status_code}")

    # Wait for agent to finish
    time.sleep(15)
    stop.set()

    # Verify we got expected event types
    event_types = [e["type"] for e in events]
    print(f"  Event types received: {event_types}")

    assert "token" in event_types, "Expected token events from LLM"
    assert "tool_start" in event_types, "Expected tool_start event"
    print("  PASS")


def main():
    print("=" * 60)
    print("E2E API Test")
    print("=" * 60)

    app = create_app()
    port = 18765
    base_url = f"http://127.0.0.1:{port}"

    start_server(app, port)

    test_health(base_url)
    test_chat_and_stream(base_url)

    print("\n" + "=" * 60)
    print("All E2E API tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run health test only (doesn't need LLM)**

Run: `poetry run python -c "
from stock_adviser.api.app import create_app
from fastapi.testclient import TestClient
client = TestClient(create_app())
r = client.get('/health')
print(r.json())
"`
Expected: `{'status': 'ok'}`

- [ ] **Step 3: Commit**

```bash
git add scripts/e2e_api_test.py
git commit -m "feat: add e2e API test script for SSE streaming"
```

---

### Task 11: Run All Checks and Final Commit

- [ ] **Step 1: Run the full check suite**

Run: `make check`
Expected: lint, test, typecheck all pass

- [ ] **Step 2: Fix any lint issues**

If ruff reports formatting issues, run `poetry run ruff format src/ tests/ scripts/` and re-stage.

- [ ] **Step 3: Update AGENTS.md module map**

Add new modules to the module map section in `AGENTS.md`:

```markdown
- `server.py` — FastAPI server entry point
- `api/app.py` — FastAPI app factory (create_app), CORS, session store
- `api/session.py` — In-memory session store (conversation history per session_id)
- `api/routes/health.py` — GET /health
- `api/routes/chat.py` — POST /chat (accept message, trigger agent)
- `api/routes/stream.py` — GET /stream/{session_id} (SSE endpoint)
- `events/types.py` — SSE event dataclasses (Token, ChartUpdate, TableUpdate, etc.)
- `events/router.py` — Maps tool results to dashboard SSE events
```

- [ ] **Step 4: Commit AGENTS.md update**

```bash
git add AGENTS.md
git commit -m "chore: update AGENTS.md with API and events module map"
```
