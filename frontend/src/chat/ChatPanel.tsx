import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
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
    <div className="flex flex-col bg-gray-900 h-full">
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
              <div className="bg-gray-800/50 rounded-lg px-3 py-2 text-sm text-gray-300 prose prose-invert prose-sm max-w-none prose-p:my-1 prose-headings:my-2 prose-ul:my-1 prose-ol:my-1 prose-li:my-0.5">
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              </div>
            )}
            {msg.role === "status" && (
              <div className="flex items-center gap-2 text-xs text-teal-400/70 italic px-1 py-1">
                <span className="inline-block w-1.5 h-1.5 bg-teal-400 rounded-full animate-pulse" />
                {msg.content}
              </div>
            )}
          </div>
        ))}
        {isAgentTyping && (
          <div className="flex items-center gap-2 text-xs text-teal-400 animate-pulse px-1">
            <span className="inline-block w-1.5 h-1.5 bg-teal-400 rounded-full" />
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
