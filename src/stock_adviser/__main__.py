"""Run the stock adviser agent in a conversational REPL with streaming output."""

import asyncio

from langchain_core.messages import BaseMessage, HumanMessage

from stock_adviser.streaming import StateEvent, TokenEvent, ToolResultEvent, ToolStartEvent, stream_events

# ANSI colour codes for terminal output
DIM = "\033[2m"
RESET = "\033[0m"


def get_greeting_message() -> HumanMessage:
    """Build the initial message that triggers the agent's greeting.

    Later this can check long-term memory to distinguish a first-time user
    from a returning one and adjust the prompt accordingly.
    """
    return HumanMessage(content="Greet the user and briefly explain what you can help with.")


async def stream_to_terminal(messages: list[BaseMessage]) -> list[BaseMessage]:
    """Consume stream events and render them to the terminal.

    Returns the updated message list for conversation history.
    """
    streaming_started = False
    final_messages = messages  # fallback

    async for event in stream_events(messages):
        if isinstance(event, TokenEvent):
            if not streaming_started:
                print("\nAssistant: ", end="", flush=True)
                streaming_started = True
            print(event.content, end="", flush=True)

        elif isinstance(event, ToolStartEvent):
            print(f"\n{DIM}  ↳ {event.status}{RESET}", flush=True)
            streaming_started = False  # Reset so next text gets "Assistant:" prefix

        elif isinstance(event, ToolResultEvent):
            print(f"{DIM}  ✓ Done{RESET}", flush=True)

        elif isinstance(event, StateEvent):
            final_messages = event.messages

    if streaming_started:
        print()  # Final newline after streamed content

    return final_messages


async def amain() -> None:
    # Generate greeting with streaming
    messages = await stream_to_terminal([get_greeting_message()])

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_input or user_input.lower() in ("quit", "exit"):
            break

        messages.append(HumanMessage(content=user_input))
        messages = await stream_to_terminal(messages)


def main() -> None:
    asyncio.run(amain())


if __name__ == "__main__":
    main()
