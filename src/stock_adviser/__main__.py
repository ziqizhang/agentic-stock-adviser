"""Run the stock adviser agent in a conversational loop with streaming output."""

from langchain_core.messages import AIMessageChunk, HumanMessage, ToolMessage

from stock_adviser.graph import graph, tools

# ANSI colour codes for terminal output
DIM = "\033[2m"
RESET = "\033[0m"
DEFAULT_TOOL_STATUS = "Working on it..."

# Build status lookup from tool metadata so each tool owns its own message
TOOL_STATUS: dict[str, str] = {t.name: t.metadata.get("status", DEFAULT_TOOL_STATUS) for t in tools if t.metadata}


def get_greeting_message() -> HumanMessage:
    """Build the initial message that triggers the agent's greeting.

    Later this can check long-term memory to distinguish a first-time user
    from a returning one and adjust the prompt accordingly.
    """
    return HumanMessage(content="Greet the user and briefly explain what you can help with.")


def stream_response(messages: list) -> list:
    """Stream a graph response, printing tokens as they arrive.

    Uses dual stream mode: 'messages' for real-time token display,
    'values' to capture the final state for conversation history.

    Returns the updated full message list.
    """
    streaming_started = False
    final_messages = messages  # fallback

    for event in graph.stream(
        {"messages": messages},
        stream_mode=["messages", "values"],
    ):
        # 'values' events give us the full state snapshot
        if isinstance(event, tuple) and event[0] == "values":
            state_snapshot = event[1]
            if "messages" in state_snapshot:
                final_messages = state_snapshot["messages"]
            continue

        # 'messages' events are (stream_mode_key, (chunk, metadata))
        if isinstance(event, tuple) and event[0] == "messages":
            chunk, metadata = event[1]

            # AI token chunks — print as they arrive
            if isinstance(chunk, AIMessageChunk):
                if chunk.content:
                    if not streaming_started:
                        print("\nAssistant: ", end="", flush=True)
                        streaming_started = True
                    print(chunk.content, end="", flush=True)

                # Tool call chunks — show which tool is being invoked
                if chunk.tool_call_chunks:
                    for tc in chunk.tool_call_chunks:
                        if tc.get("name"):
                            status = TOOL_STATUS.get(tc["name"], DEFAULT_TOOL_STATUS)
                            print(f"\n{DIM}  ↳ {status}{RESET}", flush=True)
                            streaming_started = False  # Reset so next text gets "Assistant:" prefix

            # Tool result messages
            elif isinstance(chunk, ToolMessage):
                print(f"{DIM}  ✓ Done{RESET}", flush=True)

    if streaming_started:
        print()  # Final newline after streamed content

    return final_messages


def main() -> None:
    # Generate greeting with streaming
    messages = stream_response([get_greeting_message()])

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_input or user_input.lower() in ("quit", "exit"):
            break

        messages.append(HumanMessage(content=user_input))
        messages = stream_response(messages)


if __name__ == "__main__":
    main()
