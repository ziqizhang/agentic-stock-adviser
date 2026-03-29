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
