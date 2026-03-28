"""Run the stock adviser agent in a conversational loop."""

from langchain_core.messages import HumanMessage

from stock_adviser.graph import graph


def get_greeting_message() -> HumanMessage:
    """Build the initial message that triggers the agent's greeting.

    Later this can check long-term memory to distinguish a first-time user
    from a returning one and adjust the prompt accordingly.
    """
    return HumanMessage(content="Greet the user and briefly explain what you can help with.")


def main() -> None:
    # Generate greeting
    result = graph.invoke({"messages": [get_greeting_message()]})
    messages: list = result["messages"]
    print(f"Assistant: {messages[-1].content}")

    while True:
        user_input = input("\nYou: ").strip()
        if not user_input or user_input.lower() in ("quit", "exit"):
            break

        messages.append(HumanMessage(content=user_input))
        result = graph.invoke({"messages": messages})
        messages = result["messages"]
        print(f"\nAssistant: {messages[-1].content}")


if __name__ == "__main__":
    main()
