"""E2E conversation test — drives the graph with scripted user messages."""

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from stock_adviser.graph import graph


def run_turn(messages: list, user_input: str) -> list:
    """Send a user message through the graph and return updated message history."""
    messages.append(HumanMessage(content=user_input))
    result = graph.invoke({"messages": messages})
    return result["messages"]


def print_new_messages(messages: list, prev_count: int) -> None:
    """Print messages added since prev_count."""
    for msg in messages[prev_count:]:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            for tc in msg.tool_calls:
                print(f"  [Tool Call] {tc['name']}({tc['args']})")
        elif isinstance(msg, ToolMessage):
            content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
            print(f"  [Tool Result] {content}")
        elif isinstance(msg, AIMessage):
            print(f"  Assistant: {msg.content}")
        elif isinstance(msg, HumanMessage):
            print(f"  You: {msg.content}")


def main() -> None:
    print("=" * 60)
    print("E2E Conversation Test")
    print("=" * 60)

    conversations = [
        # --- Ambiguity / restraint tests (fresh conversation) ---
        {
            "name": "Vague request (fresh) — should ask clarifying question",
            "turns": ["Tell me about Amazon"],
            "expect": "Should NOT call tools. Should ask what the user wants to know.",
        },
        # --- Ambiguity tests AFTER greeting (mimics real REPL) ---
        {
            "name": "Vague request AFTER greeting — should still ask",
            "turns": [
                "Greet the user and briefly explain what you can help with.",
                "How's Google?",
            ],
            "expect": "Greeting first, then should NOT call tools for vague follow-up.",
        },
        {
            "name": "Another vague request AFTER greeting",
            "turns": [
                "Greet the user and briefly explain what you can help with.",
                "What do you think about Tesla?",
            ],
            "expect": "Greeting first, then should NOT call tools.",
        },
        # --- Specific requests — should act immediately ---
        {
            "name": "Specific: price only",
            "turns": ["What's the price of MSFT?"],
            "expect": "Should call get_stock_price only.",
        },
        {
            "name": "Specific: full analysis requested",
            "turns": ["Give me a full analysis of Apple — price and fundamentals"],
            "expect": "Should call both get_stock_price and get_fundamentals.",
        },
        # --- Greeting ---
        {
            "name": "Greeting",
            "turns": ["Greet the user and briefly explain what you can help with."],
            "expect": "Should NOT call tools. Should describe capabilities.",
        },
        # --- Error handling ---
        {
            "name": "Unknown ticker",
            "turns": ["Get me the price of XYZXYZ123"],
            "expect": "Should call get_stock_price, get error, explain gracefully.",
        },
    ]

    for conv in conversations:
        print(f"\n{'─' * 60}")
        print(f"Scenario: {conv['name']}")
        print(f"Expected: {conv['expect']}")
        print(f"{'─' * 60}")
        messages: list = []
        for turn in conv["turns"]:
            prev_count = len(messages)
            print(f"\n  You: {turn}")
            messages = run_turn(messages, turn)
            new_msgs = messages[prev_count + 1 :]
            print_new_messages(messages, prev_count + 1)
            # Report whether tools were called
            tool_calls = [m for m in new_msgs if isinstance(m, AIMessage) and m.tool_calls]
            if tool_calls:
                names = [tc["name"] for m in tool_calls for tc in m.tool_calls]
                print(f"\n  >> TOOLS CALLED: {names}")
            else:
                print("\n  >> NO TOOLS CALLED (text-only response)")


if __name__ == "__main__":
    main()
