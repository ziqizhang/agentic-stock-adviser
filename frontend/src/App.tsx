import { useState, useRef, useCallback, useEffect } from "react";
import { ChatPanel, SESSION_ID } from "./chat/ChatPanel";
import { Dashboard } from "./dashboard/Dashboard";
import { SettingsModal } from "./settings/SettingsModal";
import { getSettingsStatus } from "./settings/api";
import { useSSE } from "./stream/useSSE";
import { useStore } from "./store";

const MIN_CHAT_WIDTH = 280;
const DEFAULT_CHAT_WIDTH = 360;

function App() {
  useSSE(SESSION_ID);

  const llmConfigured = useStore((s) => s.llmConfigured);
  const setLlmConfigured = useStore((s) => s.setLlmConfigured);
  const setSettingsOpen = useStore((s) => s.setSettingsOpen);

  const [chatWidth, setChatWidth] = useState(DEFAULT_CHAT_WIDTH);
  const dragging = useRef(false);

  // Check config on mount
  useEffect(() => {
    getSettingsStatus().then((configured) => {
      setLlmConfigured(configured);
      if (!configured) {
        setSettingsOpen(true);
      }
    });
  }, [setLlmConfigured, setSettingsOpen]);

  const onMouseDown = useCallback(() => {
    dragging.current = true;
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";

    const onMouseMove = (e: MouseEvent) => {
      if (!dragging.current) return;
      const maxWidth = window.innerWidth / 2;
      const newWidth = Math.min(maxWidth, Math.max(MIN_CHAT_WIDTH, window.innerWidth - e.clientX));
      setChatWidth(newWidth);
    };

    const onMouseUp = () => {
      dragging.current = false;
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
    };

    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
  }, []);

  return (
    <div className="h-screen bg-gray-950 text-gray-200 flex">
      {/* Gear icon */}
      <button
        onClick={() => setSettingsOpen(true)}
        className="fixed top-3 right-3 z-40 text-gray-500 hover:text-teal-400 transition-colors"
        title="LLM Settings"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
        </svg>
      </button>

      <div className="flex-1 min-w-0 overflow-hidden">
        <Dashboard />
      </div>
      {/* Drag handle */}
      <div
        onMouseDown={onMouseDown}
        className="w-1 cursor-col-resize bg-gray-800 hover:bg-teal-400/50 transition-colors flex-shrink-0"
      />
      <div style={{ width: chatWidth }} className="flex-shrink-0 border-l border-gray-800">
        <ChatPanel />
      </div>

      <SettingsModal />
    </div>
  );
}

export default App;
