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
│         │     (server detects new message, runs agent)    │         │
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
- The SSE stream detects new messages and runs the agent
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

## Internal Data Flow

This shows what happens inside the server when a message arrives:

```
                    ┌──────────────────────────────────────────────────┐
                    │                    SERVER                        │
                    │                                                  │
  POST /chat ──────>│  SessionStore                                    │
  {message: "..."}  │  ┌─────────────────┐                            │
                    │  │ session-123:     │                            │
        append ────>│  │  [HumanMessage]  │<──── read ────┐           │
        only        │  │  [AIMessage]     │               │           │
                    │  │  [HumanMessage]  │◄── new!       │           │
                    │  └─────────────────┘               │           │
                    │                                     │           │
                    │  GET /stream/session-123             │           │
                    │  ┌─────────────────────────────────────┐        │
                    │  │ _event_generator (polling loop)     │        │
                    │  │                                     │        │
                    │  │  1. Poll session store ─────────────┘        │
                    │  │  2. Detect new message (count changed)       │
                    │  │  3. Run agent via stream_events()            │
                    │  │     │                                        │
                    │  │     ├─ TokenEvent ──────> Token SSE          │──> browser
                    │  │     ├─ ToolStartEvent ──> ToolStart SSE     │──> browser
                    │  │     ├─ ToolResultEvent ─> route_tool_result  │
                    │  │     │   ├─ StockOpened SSE                   │──> browser
                    │  │     │   └─ ChartUpdate SSE                   │──> browser
                    │  │     └─ StateEvent ──────> update session     │
                    │  │  4. Emit Done SSE                            │──> browser
                    │  │  5. Back to polling...                       │
                    │  └─────────────────────────────────────┘        │
                    └──────────────────────────────────────────────────┘
```

Key insight: **POST /chat and GET /stream communicate through the SessionStore.**
POST writes to it, GET reads from it. They never call each other directly.
This is the producer/consumer pattern — the same principle behind message queues.

## The Bug We Had (and the Lesson)

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
