const API_BASE = "";

export interface LLMSettings {
  provider: string;
  model: string;
  api_key: string;
  azure_endpoint: string | null;
  azure_api_version: string | null;
  azure_deployment: string | null;
}

export async function getSettingsStatus(): Promise<boolean> {
  const res = await fetch(`${API_BASE}/settings/status`);
  const data = await res.json();
  return data.configured;
}

export async function getSettings(): Promise<LLMSettings> {
  const res = await fetch(`${API_BASE}/settings`);
  if (!res.ok) throw new Error("Not configured");
  return res.json();
}

export async function saveSettings(settings: LLMSettings): Promise<void> {
  const res = await fetch(`${API_BASE}/settings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(settings),
  });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data.detail || "Failed to save settings");
  }
}
