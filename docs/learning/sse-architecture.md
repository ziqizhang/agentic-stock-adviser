# SSE Architecture for Agent UIs

A reference guide explaining how Server-Sent Events (SSE) work in the context of
building web UIs for LLM agents, and the architectural decisions made in this project.

## What is SSE?

SSE (Server-Sent Events) is a browser-native protocol for **one-way server→browser
streaming** over a persistent HTTP connection. The browser opens a GET request that
never "finishes" — the server keeps sending events down the wire as they happen.

```
Browser                          Server
   |                                |
   |--- GET /stream/session-123 --->|   (opens persistent connection)
   |                                |
   |<-- event: token "Hello" ------|
   |<-- event: token " world" -----|   (server pushes events any time)
   |<-- event: tool_start ---------|
   |<-- event: chart_update -------|
   |<-- event: done ---------------|
   |                                |
   |   (connection stays open...)   |
   |                                |
```

Key properties:
- **One-way**: server→browser only. Browser cannot send data back on this connection.
- **Auto-reconnect**: if the connection drops, the browser reconnects automatically.
- **Text-based**: each event is a line of text (`data: {"type": "token", ...}`).
- **Native API**: `new EventSource(url)` — no libraries needed.

## Two Approaches to Agent Streaming

### Approach A: Single streaming POST

Used by OpenAI's API, simpler chat UIs.

```
┌─────────┐         POST /chat (streaming response)        ┌─────────┐
│         │ ─────────────────────────────────────────────>  │         │
│ Browser │ <── token ── token ── tool ── token ── done ── │ Server  │
│         │ <──────────────────────────────────────────────  │         │
└─────────┘         (connection closes after done)          └─────────┘
```

- One request = one message = one response stream
- Simple: message and response share the same HTTP connection
- Limitation: each message needs a new connection
- Limitation: server cannot push events outside of a request cycle

### Approach B: Separate trigger + persistent stream (what we use)

Used by more complex UIs that need ongoing server→browser communication.

```
┌─────────┐                                                 ┌─────────┐
│         │ ── GET /stream/session-123 ──────────────────>  │         │
│         │ <── : connected ────────────────────────────── │         │
│         │                                                 │         │
│         │     (SSE connection stays open permanently)     │         │
│         │                                                 │         │
│ Browser │ ── POST /chat {message: "Price of AAPL?"} ──>  │ Server  │
│         │ <── 202 accepted ────────────────────────────  │         │
│         │                                                 │         │
│         │     (server is signalled, runs agent)           │         │
│         │                                                 │         │
│         │ <── tool_start: "Fetching price..." ──────────  │         │
│         │ <── stock_opened: AAPL ───────────────────────  │         │
│         │ <── chart_update: {prices: [248.8]} ──────────  │         │
│         │ <── token: "Apple Inc..." ────────────────────  │         │
│         │ <── token: "...current price is $248.80" ─────  │         │
│         │ <── done ─────────────────────────────────────  │         │
│         │                                                 │         │
│         │     (still open, waiting for next message...)   │         │
│         │                                                 │         │
│         │ ── POST /chat {message: "Compare to MSFT"} ──>  │         │
│         │ <── 202 accepted ────────────────────────────  │         │
│         │ <── tool_start: "Fetching price..." ──────────  │         │
│         │ <── ... more events ... ──────────────────────  │         │
│         │ <── done ─────────────────────────────────────  │         │
└─────────┘                                                 └─────────┘
```

- SSE connection opens once, persists across all messages
- POST /chat is a "mailbox" — drops off the message and returns immediately
- The SSE stream is **signalled** to wake up and run the agent
- Events flow through the single persistent pipe

## Why We Chose Approach B

Approach A ties the stream to a single request. Once the response ends, there is no
way for the server to push more data until the browser sends another request. This
creates problems for a dashboard:

1. **Dashboard updates span multiple messages.** The user asks "Price of AAPL?" and
   later "Show fundamentals." Both update the same stock tab. With Approach A, each
   response stream is independent — there is no shared channel for ongoing updates.

2. **Server-initiated events.** In the future, the agent might proactively push
   alerts ("AAPL dropped 5%!") without the user asking. Approach A has no way to
   do this — there is no open connection to push to.

3. **Resilience.** If a POST request fails (network blip), the SSE connection is
   unaffected. The user can retry the message and events will arrive on the same
   stream. With Approach A, a failed POST means a lost response.

4. **WebSocket migration path.** When we eventually need bidirectional communication
   (browser→server streaming), only two files change: the backend SSE route becomes
   a WebSocket route, and the frontend `useSSE` hook becomes a `useWebSocket` hook.
   The rest of the architecture (store, event routing, components) stays the same.

---

## How a Token Travels: The Full Chain

This is the core of the architecture. A single token is born inside the LLM and
travels through 7 stages before the user sees it rendered in the browser. Every
stage is **async** — no threads, no queues, no polling.

If you're used to classic client-server (request → process → response), the key
difference is: **the response never ends.** The server keeps the connection open and
pushes data whenever it has something to say. Think of it as a radio broadcast that
the browser tunes into.

### The 7 stages

```
Stage 1          Stage 2          Stage 3          Stage 4
LLM generates    LangGraph        streaming.py     stream.py
a token chunk    astream()        classifies       converts to
                 yields it        the event        SSE format
    │                │                │                │
    ▼                ▼                ▼                ▼

 ┌──────┐      ┌──────────┐    ┌────────────┐    ┌──────────┐
 │ LLM  │─────>│ LangGraph│───>│ stream_    │───>│ _event_  │
 │ .a   │chunk │ .astream │    │ events()   │    │ generator│
 │invoke│      │   ()     │    │            │    │   ()     │
 └──────┘      └──────────┘    └────────────┘    └──────────┘
   OpenAI        graph.py       streaming.py      stream.py
   (remote)     (in-process)    (in-process)      (in-process)

                                                       │
    ┌──────────────────────────────────────────────────┘
    │
    ▼
Stage 5          Stage 6          Stage 7
sse-starlette    Browser          React
writes to HTTP   EventSource      re-renders
response         fires event      the UI

    │                │                │
    ▼                ▼                ▼

 ┌──────────┐    ┌──────────┐    ┌──────────┐
 │ Event    │───>│ Event    │───>│ Zustand  │───> ChatPanel
 │ Source   │HTTP│ Source   │JS  │ store    │     re-renders
 │ Response │wire│ onmessage│    │ setState │     with new
 └──────────┘    └──────────┘    └──────────┘     token
  sse-starlette   browser API     useSSE.ts
  (in-process)    (browser)       (browser)
```

### What happens at each stage

**Stage 1 — LLM generates a token** (`graph.py:agent()`)
The LLM (OpenAI API) generates text in small chunks. We call it with
`await llm.ainvoke(messages)` — the `a` prefix means async. The LLM returns
an `AIMessage`, but LangGraph intercepts the stream to give us token-by-token
access.

**Stage 2 — LangGraph streams the chunk** (`graph.py` compiled graph)
`graph.astream(messages, stream_mode=["messages", "values"])` yields two kinds
of events as they happen:
- `("messages", (chunk, metadata))` — individual token chunks, tool calls
- `("values", {...})` — full state snapshots after each node completes

This is like subscribing to a live feed of the agent's internal monologue.

**Stage 3 — Classification** (`streaming.py:stream_events()`)
An async generator that reads the raw LangGraph stream and classifies each
event into our domain types:
- `AIMessageChunk` with `.content` → `TokenEvent`
- `AIMessageChunk` with `.tool_call_chunks` → `ToolStartEvent`
- `ToolMessage` → `ToolResultEvent`
- State snapshot with messages → `StateEvent`

**Stage 4 — SSE formatting** (`stream.py:_event_generator()`)
Converts our domain events into SSE-formatted dicts that `sse-starlette`
understands:
- `TokenEvent` → `{"event": "token", "data": "..."}`
- `ToolStartEvent` → `{"event": "tool_start", "data": "..."}`
- Tool results also pass through `route_tool_result()` to generate
  dashboard-specific events (chart updates, stock cards).

**Stage 5 — HTTP wire** (`sse-starlette` library)
`EventSourceResponse` wraps our async generator. Each time we `yield` a dict,
it serialises it as an SSE text line and writes it to the HTTP response.
The response is never "finished" — it stays open, writing lines as they come.

**Stage 6 — Browser receives** (`EventSource` API)
The browser's native `EventSource` object listens on the open connection.
Each SSE line triggers an `onmessage` callback with the parsed event data.

**Stage 7 — React re-renders** (`useSSE.ts` → Zustand store → components)
The SSE callback dispatches the event to the Zustand store, which appends
the token to the current message. React detects the state change and
re-renders `ChatPanel` with the new text — one token at a time.

### Classic comparison

If you're used to REST APIs, here's the mental model shift:

```
Classic REST:
  Browser ──POST──> Server ──process──> Response (one shot, connection closes)

This architecture:
  Browser ──GET──> Server (connection stays open forever)
  Browser ──POST──> Server ──202──> (just stores the message)
                    Server: "oh, new message!" (asyncio.Event fires)
                    Server ──stream tokens──> open GET connection ──> Browser
                    Server ──stream tokens──> open GET connection ──> Browser
                    Server ──stream tokens──> open GET connection ──> Browser
                    Server ──done──> open GET connection ──> Browser
                    (connection still open, waiting for next message...)
```

The POST and GET are **decoupled**. POST is fire-and-forget. GET is a live
data feed. They communicate through the `SessionStore` — POST writes to it,
GET reads from it.

---

## The Signalling Mechanism: How POST Wakes Up GET

This is the coordination layer that makes the decoupled design work.
Without it, the SSE generator would have to poll the session store in a
loop, which wastes CPU and introduces latency.

### The problem with polling (what we had before)

```
  _event_generator:                          POST /chat:
    loop:                                      append message
      count = len(session.messages)            return 202
      if count > last_count:
        run agent...
      else:
        sleep(0.1)  ← waste 100ms, then check again
```

Polling has two problems:
1. **Latency**: up to 100ms delay before the generator notices a new message.
2. **Race condition**: `EventSourceResponse` schedules the generator lazily
   via `anyio.start_soon`. The POST can arrive *between* route handler setup
   and generator first execution. If `last_count` initialises to the
   already-incremented value, the generator never sees the change.

### The solution: `asyncio.Event` signalling (what we have now)

```python
# session.py — one Event per session
class SessionStore:
    def notify(self, session_id):       # called by POST /chat
        self._events[session_id].set()  # "wake up!"

    async def wait_for_message(self, session_id):  # called by SSE generator
        await self._events[session_id].wait()       # sleep until set()
        self._events[session_id].clear()            # reset for next time
```

```
  _event_generator:                          POST /chat:
    loop:                                      append message
      await wait_for_message()  ← sleeps        notify()  ← wakes it up
      (woken up instantly!)                    return 202
      run agent...
```

This is the **producer/consumer pattern** with an event signal:
- **Producer** (POST /chat): stores the message, fires the signal
- **Consumer** (SSE generator): sleeps on the signal, wakes up when fired
- **No polling**, **no race conditions**, **no wasted CPU**

The signal is like a doorbell. The SSE generator is sleeping at the door.
When POST rings the bell, the generator wakes up immediately and processes
the message. No need to keep checking the mailbox every 100ms.

### The files involved

| File | Role | Key function |
|------|------|-------------|
| `session.py` | Shared state + signal | `notify()`, `wait_for_message()` |
| `chat.py` | Producer | Calls `append()` then `notify()` |
| `stream.py` | Consumer | Calls `wait_for_message()` then `stream_events()` |

---

## Internal Data Flow (Detailed)

This shows what happens inside the server when a message arrives:

```
                    ┌──────────────────────────────────────────────────────┐
                    │                    SERVER                            │
                    │                                                      │
  POST /chat ──────>│  SessionStore                                        │
  {message: "..."}  │  ┌─────────────────┐                                │
                    │  │ session-123:     │                                │
        append ────>│  │  [HumanMessage]  │<──── read ────┐               │
        + notify    │  │  [AIMessage]     │               │               │
                    │  │  [HumanMessage]  │◄── new!       │               │
                    │  └────────┬────────┘               │               │
                    │           │ asyncio.Event.set()      │               │
                    │           │ (doorbell rings)         │               │
                    │           ▼                          │               │
                    │  GET /stream/session-123             │               │
                    │  ┌──────────────────────────────────────┐           │
                    │  │ _event_generator                      │           │
                    │  │                                       │           │
                    │  │  1. await wait_for_message() ◄────────┘           │
                    │  │     (wakes up instantly when notified)             │
                    │  │  2. Read messages from session store               │
                    │  │  3. async for event in stream_events():            │
                    │  │     │                                              │
                    │  │     │  graph.astream() runs the agent:             │
                    │  │     │  ┌─────────────────────────────────┐        │
                    │  │     │  │ LLM ──> tokens (AIMessageChunk) │        │
                    │  │     │  │ Tool calls ──> ToolMessage       │        │
                    │  │     │  │ State snapshots ──> values       │        │
                    │  │     │  └─────────────────────────────────┘        │
                    │  │     │                                              │
                    │  │     ├─ TokenEvent ──────> Token SSE        │──> browser
                    │  │     ├─ ToolStartEvent ──> ToolStart SSE   │──> browser
                    │  │     ├─ ToolResultEvent ─> route_tool_result│
                    │  │     │   ├─ StockOpened SSE                 │──> browser
                    │  │     │   └─ ChartUpdate SSE                 │──> browser
                    │  │     └─ StateEvent ──────> update session   │
                    │  │  4. Emit Done SSE                          │──> browser
                    │  │  5. Back to await wait_for_message()...    │
                    │  └───────────────────────────────────────────┘       │
                    └──────────────────────────────────────────────────────┘
```

Key insight: **POST /chat and GET /stream communicate through the SessionStore.**
POST writes to it and rings the doorbell. GET sleeps on the doorbell, wakes up,
reads the messages, runs the agent, and streams the results. They never call each
other directly. This is the producer/consumer pattern.

---

## Bugs We Had (and the Lessons)

### Bug 1: Two consumers on one queue

The original implementation had POST /chat both append the message AND run the agent:

```
  POST /chat ──> append message ──> run agent (background thread)
                                         │
                                         └── consumes all events
                                              (nowhere to send them)

  GET /stream ──> detects new message ──> tries to run agent
                                               │
                                               └── agent already ran,
                                                    nothing to stream
```

Two consumers on one queue. The background thread "ate" the work before the SSE
stream could process it. The agent ran, produced tokens and tool results, but they
went nowhere because the background thread had no SSE connection to the browser.

**The fix:** POST /chat is a mailbox, not a worker. It stores the message and returns.
The SSE stream is the sole consumer — it detects the message, runs the agent, and
streams the results directly to the browser.

**The principle:** In event-driven architectures, only one component should own the
processing of each event. Decide who the consumer is and stick to it. Having two
things try to process the same trigger creates race conditions.

### Bug 2: Sync-inside-async anti-pattern

The streaming layer originally used the synchronous `graph.stream()` inside
an `async def` generator. This blocked the entire event loop — no other
request could be processed while the agent was running. Worse, it meant we
needed thread-bridging code (queues, `call_soon_threadsafe`) to get tokens
from the sync stream into the async SSE generator.

**The fix:** Make the entire chain async:
- `llm.ainvoke()` instead of `llm.invoke()`
- `graph.astream()` instead of `graph.stream()`
- `async for` instead of `for` in the generator

**The principle:** In async Python, one synchronous call poisons the whole
pipeline. If your framework is async (FastAPI/Starlette), your LLM calls,
your graph execution, and your generators all need to be async too. "Async
all the way" is not optional — it's the architecture.

### Bug 3: Polling race condition

The polling mechanism (`sleep → check count → repeat`) had a race condition:
`EventSourceResponse` schedules the generator lazily. The POST could arrive
between route setup and generator start, causing `last_count` to initialise
to the already-incremented value. The generator would see `count == last_count`
and go back to sleep, missing the message entirely.

**The fix:** Replaced polling with `asyncio.Event` signalling (described above).
No counting, no sleeping, no race.

**The principle:** Polling is a code smell in async architectures. If you're
writing `await asyncio.sleep(N)` in a loop to check for changes, there's
almost certainly a better coordination primitive (`Event`, `Queue`, `Condition`)
that eliminates the delay and the race.

---

## SSE vs WebSocket vs Long Polling

| Feature              | SSE                  | WebSocket           | Long Polling        |
|----------------------|----------------------|---------------------|---------------------|
| Direction            | Server → Browser     | Bidirectional       | Server → Browser    |
| Browser API          | `EventSource` (native) | `WebSocket` (native) | `fetch` in a loop  |
| Auto-reconnect       | Built-in             | Manual              | Manual              |
| Protocol             | HTTP                 | WS (upgrade from HTTP) | HTTP              |
| Through proxies/CDNs | Works everywhere     | Sometimes blocked   | Works everywhere    |
| Complexity           | Low                  | Medium              | Low (but wasteful)  |
| When to use          | Agent streaming, notifications, dashboards | Chat, gaming, collaboration | Legacy, simple polling |

SSE is the right choice for agent UIs because the primary data flow is one-way
(agent→user). When we need bidirectional streaming (e.g., user interrupts the agent
mid-response), we upgrade to WebSocket — but the store/component architecture stays
the same.

---

## Reading the Code: Where to Start

If you want to trace the flow yourself, read in this order:

1. **`graph.py`** — The agent node. `await llm.ainvoke(messages)` is where tokens are born.
2. **`streaming.py`** — `stream_events()`. Calls `graph.astream()` and classifies raw events.
3. **`stream.py`** — `_event_generator()`. Awaits the signal, calls `stream_events()`, yields SSE dicts.
4. **`session.py`** — `SessionStore`. The shared mailbox with `notify()` / `wait_for_message()`.
5. **`chat.py`** — POST handler. Appends message, rings the doorbell.
6. **`frontend/src/hooks/useSSE.ts`** — Browser-side `EventSource` listener.
7. **`frontend/src/chat/ChatPanel.tsx`** — React component that renders the streamed tokens.
