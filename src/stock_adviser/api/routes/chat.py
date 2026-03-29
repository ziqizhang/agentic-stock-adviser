"""POST /chat — accept a user message for the agent.

Only appends the message to the session. The SSE stream endpoint detects the
new message and runs the agent so events can be streamed to the client.
"""

from fastapi import APIRouter, Request
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, field_validator

from stock_adviser.api.session import SessionStore

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


@router.post("/chat", status_code=202)
async def chat(body: ChatRequest, request: Request) -> dict:
    sessions: SessionStore = request.app.state.sessions
    sessions.append(body.session_id, HumanMessage(content=body.message))
    return {"status": "accepted"}
