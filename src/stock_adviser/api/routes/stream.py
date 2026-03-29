"""GET /stream/{session_id} — SSE endpoint for real-time events."""

import asyncio
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from stock_adviser.api.session import SessionStore
from stock_adviser.events.router import route_tool_result
from stock_adviser.events.types import Done, Token, ToolResult, ToolStart
from stock_adviser.streaming import (
    StateEvent,
    TokenEvent,
    ToolResultEvent,
    ToolStartEvent,
    stream_events,
)

router = APIRouter()


async def _event_generator(sessions: SessionStore, session_id: str, request: Request) -> AsyncGenerator[dict, None]:
    """Watch for new messages in the session and stream agent events as SSE.

    Polls for new messages. When a new message appears (from POST /chat),
    it runs the agent and streams events. Exits when the client disconnects.
    """
    last_count = len(sessions.get_or_create(session_id))

    # Yield an initial comment so the response headers are flushed immediately.
    yield {"comment": "connected"}

    while True:
        if await request.is_disconnected():
            break

        messages = sessions.get_or_create(session_id)
        current_count = len(messages)

        if current_count > last_count:
            last_count = current_count

            def _stream():
                return list(stream_events(messages))

            loop = asyncio.get_running_loop()
            events = await loop.run_in_executor(None, _stream)

            for event in events:
                if isinstance(event, TokenEvent):
                    yield Token(content=event.content).to_sse()

                elif isinstance(event, ToolStartEvent):
                    yield ToolStart(tool=event.tool_name, status=event.status).to_sse()

                elif isinstance(event, ToolResultEvent):
                    yield ToolResult().to_sse()
                    dashboard_events = route_tool_result(event.tool_name, event.content)
                    for de in dashboard_events:
                        yield de.to_sse()

                elif isinstance(event, StateEvent):
                    sessions.update(session_id, event.messages)
                    last_count = len(event.messages)

            yield Done().to_sse()

        await asyncio.sleep(0.1)


@router.get("/stream/{session_id}")
async def stream(session_id: str, request: Request) -> EventSourceResponse:
    sessions: SessionStore = request.app.state.sessions
    sessions.get_or_create(session_id)
    return EventSourceResponse(_event_generator(sessions, session_id, request))
