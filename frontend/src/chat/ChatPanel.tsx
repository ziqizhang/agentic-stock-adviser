import { useState, useRef, useEffect } from "react";
import { useStore } from "../store";
import { sendChatMessage } from "../stream/api";

const SESSION_ID = crypto.randomUUID();

export function ChatPanel() {
  const messages = useStore((s) => s.messages);
  const isAgentTyping = useStore((s) => s.isAgentTyping);
  const chatOpen = useStore((s) => s.chatOpen);
  const toggleChat = useStore((s) => s.toggleChat);
  const addUserMessage = useStore((s) => s.addUserMessage);

  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    const text = input.trim();
    if (!text) return;
    addUserMessage(text);
    sendChatMessage(SESSION_ID, text);
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!chatOpen) {
    return (
      <button
        onClick={toggleChat}
        className="fixed right-0 top-1/2 -translate-y-1/2 bg-gray-800 text-gray-400 px-2 py-4 rounded-l-lg hover:bg-gray-700 hover:text-teal-400 z-10"
      >
        &laquo;
      </button>
    );
  }

  return (
    <div className="w-80 border-l border-gray-800 flex flex-col bg-gray-900">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800">
        <span className="text-teal-400 font-medium text-sm">Agent</span>
        <button
          onClick={toggleChat}
          className="text-gray-500 hover:text-gray-300 text-sm"
        >
          &raquo;
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 && (
          <p className="text-gray-500 text-sm">
            Ask me about any stock to get started.
          </p>
        )}
        {messages.map((msg, i) => (
          <div key={i}>
            {msg.role === "user" && (
              <div className="bg-gray-800 rounded-lg px-3 py-2 text-sm ml-8">
                {msg.content}
              </div>
            )}
            {msg.role === "assistant" && (
              <div className="bg-gray-800/50 rounded-lg px-3 py-2 text-sm text-gray-300">
                {msg.content}
              </div>
            )}
            {msg.role === "status" && (
              <div className="text-xs text-gray-500 italic px-1">
                {msg.content}
              </div>
            )}
          </div>
        ))}
        {isAgentTyping && (
          <div className="text-xs text-teal-400 animate-pulse px-1">
            Thinking...
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="p-3 border-t border-gray-800">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about a stock..."
            className="flex-1 bg-gray-800 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-500 outline-none focus:ring-1 focus:ring-teal-400/50"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim()}
            className="bg-teal-600 hover:bg-teal-500 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-lg px-3 py-2 text-sm"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

export { SESSION_ID };
