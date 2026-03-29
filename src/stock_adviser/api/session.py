"""In-memory session store for conversation history.

Each session_id maps to a list of LangChain messages.
No persistence across restarts — designed to be swapped for
Redis/DB later via the same interface.

Thread-safe: accessed from both the async event loop (POST /chat)
and executor threads (agent streaming in GET /stream).
"""

import threading

from langchain_core.messages import BaseMessage


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, list[BaseMessage]] = {}
        self._lock = threading.Lock()

    def get_or_create(self, session_id: str) -> list[BaseMessage]:
        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = []
            return list(self._sessions[session_id])

    def append(self, session_id: str, message: BaseMessage) -> None:
        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = []
            self._sessions[session_id].append(message)

    def update(self, session_id: str, messages: list[BaseMessage]) -> None:
        with self._lock:
            self._sessions[session_id] = messages
