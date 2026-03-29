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
