import { ChatPanel, SESSION_ID } from "./chat/ChatPanel";
import { Dashboard } from "./dashboard/Dashboard";
import { useSSE } from "./stream/useSSE";

function App() {
  useSSE(SESSION_ID);

  return (
    <div className="h-screen bg-gray-950 text-gray-200 flex">
      <Dashboard />
      <ChatPanel />
    </div>
  );
}

export default App;
