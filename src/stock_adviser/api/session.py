"""In-memory session store for conversation history.

Each session_id maps to a list of LangChain messages plus an asyncio.Event
used to notify the SSE stream when a new message arrives.

No persistence across restarts — designed to be swapped for
a LangGraph checkpointer (Pillar 4) via the same interface.

Single-threaded: all access is on the async event loop. The sync
tools run in executor threads but don't touch the session store.
"""

import asyncio

from langchain_core.messages import BaseMessage


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, list[BaseMessage]] = {}
        self._events: dict[str, asyncio.Event] = {}

    def _ensure(self, session_id: str) -> None:
        if session_id not in self._sessions:
            self._sessions[session_id] = []
            self._events[session_id] = asyncio.Event()

    def get_messages(self, session_id: str) -> list[BaseMessage]:
        self._ensure(session_id)
        return list(self._sessions[session_id])

    def append(self, session_id: str, message: BaseMessage) -> None:
        self._ensure(session_id)
        self._sessions[session_id].append(message)

    def notify(self, session_id: str) -> None:
        """Signal the SSE stream that a new message is available."""
        self._ensure(session_id)
        self._events[session_id].set()

    async def wait_for_message(self, session_id: str) -> None:
        """Block until notify() is called for this session."""
        self._ensure(session_id)
        await self._events[session_id].wait()
        self._events[session_id].clear()

    def update(self, session_id: str, messages: list[BaseMessage]) -> None:
        self._ensure(session_id)
        self._sessions[session_id] = messages
