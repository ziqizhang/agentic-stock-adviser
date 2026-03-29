const API_BASE = "";

export async function sendChatMessage(sessionId: string, message: string): Promise<void> {
  await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message }),
  });
}
