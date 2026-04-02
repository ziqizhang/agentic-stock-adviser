"""GET /stream/{session_id} — SSE endpoint for real-time events."""

import logging
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from stock_adviser.api.session import SessionStore
from stock_adviser.events.router import route_tool_result
from stock_adviser.events.types import Done, Error, Token, ToolResult, ToolStart
from stock_adviser.streaming import (
    StateEvent,
    TokenEvent,
    ToolResultEvent,
    ToolStartEvent,
    stream_events,
)

router = APIRouter()
logger = logging.getLogger(__name__)


async def _event_generator(sessions: SessionStore, session_id: str, request: Request) -> AsyncGenerator[dict, None]:
    """Wait for new messages and stream agent events as SSE.

    Uses asyncio.Event (set by POST /chat) instead of polling.
    No busy-waiting, no race conditions.
    """
    yield {"comment": "connected"}

    while True:
        if await request.is_disconnected():
            break

        await sessions.wait_for_message(session_id)

        messages = sessions.get_messages(session_id)

        try:
            async for event in stream_events(messages):
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

            yield Done().to_sse()
        except Exception as exc:
            logger.exception("Error during agent streaming")
            yield Error(message=str(exc)).to_sse()
            yield Done().to_sse()


@router.get("/stream/{session_id}")
async def stream(session_id: str, request: Request) -> EventSourceResponse:
    sessions: SessionStore = request.app.state.sessions
    sessions.get_messages(session_id)
    return EventSourceResponse(_event_generator(sessions, session_id, request))
