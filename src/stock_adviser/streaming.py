"""Stream event classification for the agent graph.

Iterates the LangGraph dual stream (messages + values) and yields typed events.
Consumers (REPL, FastAPI, WebSocket) decide how to render each event type.
"""

from collections.abc import Generator
from dataclasses import dataclass

from langchain_core.messages import AIMessageChunk, BaseMessage, ToolMessage

from stock_adviser.graph import graph, tools

DEFAULT_TOOL_STATUS = "Working on it..."

# Build status lookup from tool metadata so each tool owns its own message
_TOOL_STATUS: dict[str, str] = {t.name: t.metadata.get("status", DEFAULT_TOOL_STATUS) for t in tools if t.metadata}


@dataclass
class TokenEvent:
    """A chunk of text from the LLM response."""

    content: str


@dataclass
class ToolStartEvent:
    """The LLM has requested a tool call."""

    tool_name: str
    status: str


@dataclass
class ToolResultEvent:
    """A tool has returned its result."""

    pass


@dataclass
class StateEvent:
    """A full state snapshot from the graph (contains updated message history)."""

    messages: list[BaseMessage]


StreamEvent = TokenEvent | ToolStartEvent | ToolResultEvent | StateEvent


def stream_events(messages: list[BaseMessage]) -> Generator[StreamEvent, None, None]:
    """Iterate the graph stream and yield classified events.

    Uses dual stream mode: 'messages' for real-time chunks,
    'values' to capture state snapshots for conversation history.
    """
    for event in graph.stream(
        {"messages": messages},
        stream_mode=["messages", "values"],
    ):
        if not isinstance(event, tuple):
            continue

        mode, payload = event

        if mode == "values" and isinstance(payload, dict) and "messages" in payload:
            yield StateEvent(messages=payload["messages"])

        elif mode == "messages":
            chunk, _metadata = payload

            if isinstance(chunk, AIMessageChunk):
                if chunk.content:
                    yield TokenEvent(content=chunk.content)

                if chunk.tool_call_chunks:
                    for tc in chunk.tool_call_chunks:
                        if tc.get("name"):
                            status = _TOOL_STATUS.get(tc["name"], DEFAULT_TOOL_STATUS)
                            yield ToolStartEvent(tool_name=tc["name"], status=status)

            elif isinstance(chunk, ToolMessage):
                yield ToolResultEvent()
