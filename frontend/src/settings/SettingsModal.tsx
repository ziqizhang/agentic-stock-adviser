import { useState, useEffect } from "react";
import { useStore } from "../store";
import { getSettings, saveSettings, type LLMSettings } from "./api";

const PROVIDERS = [
  { value: "openai", label: "OpenAI" },
  { value: "azure_openai", label: "Azure OpenAI" },
  { value: "anthropic", label: "Anthropic" },
  { value: "google", label: "Google Gemini" },
];

export function SettingsModal() {
  const settingsOpen = useStore((s) => s.settingsOpen);
  const setSettingsOpen = useStore((s) => s.setSettingsOpen);
  const setLlmConfigured = useStore((s) => s.setLlmConfigured);

  const [provider, setProvider] = useState("openai");
  const [model, setModel] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [azureEndpoint, setAzureEndpoint] = useState("");
  const [azureApiVersion, setAzureApiVersion] = useState("");
  const [azureDeployment, setAzureDeployment] = useState("");
  const [maskedKey, setMaskedKey] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const isAzure = provider === "azure_openai";

  // Load existing settings when modal opens
  useEffect(() => {
    if (!settingsOpen) return;
    getSettings()
      .then((s) => {
        setProvider(s.provider);
        setModel(s.model);
        setMaskedKey(s.api_key);
        setApiKey("");
        setAzureEndpoint(s.azure_endpoint || "");
        setAzureApiVersion(s.azure_api_version || "");
        setAzureDeployment(s.azure_deployment || "");
      })
      .catch(() => {
        // Not configured yet — keep defaults
      });
  }, [settingsOpen]);

  if (!settingsOpen) return null;

  const handleSave = async () => {
    setError("");
    setSaving(true);
    try {
      const settings: LLMSettings = {
        provider,
        model,
        api_key: apiKey,
        azure_endpoint: isAzure ? azureEndpoint : null,
        azure_api_version: isAzure ? azureApiVersion : null,
        azure_deployment: isAzure ? azureDeployment : null,
      };
      await saveSettings(settings);
      setLlmConfigured(true);
      setSettingsOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  const canSave = model.trim() && (apiKey.trim() || maskedKey) && (!isAzure || (azureEndpoint.trim() && azureApiVersion.trim() && azureDeployment.trim()));

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-gray-900 border border-gray-700 rounded-xl shadow-2xl w-full max-w-md p-6 space-y-4">
        <h2 className="text-lg font-semibold text-gray-100">LLM Settings</h2>
        <p className="text-sm text-gray-400">
          Configure your LLM provider to get started. Make sure the model name
          exactly matches your provider's naming (e.g. <code className="text-teal-400">gpt-4o</code>,{" "}
          <code className="text-teal-400">claude-sonnet-4-20250514</code>).
        </p>

        {/* Provider */}
        <label className="block">
          <span className="text-sm text-gray-400">Provider</span>
          <select
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
            className="mt-1 block w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 outline-none focus:ring-1 focus:ring-teal-400/50"
          >
            {PROVIDERS.map((p) => (
              <option key={p.value} value={p.value}>
                {p.label}
              </option>
            ))}
          </select>
        </label>

        {/* Model */}
        <label className="block">
          <span className="text-sm text-gray-400">
            {isAzure ? "Deployment name" : "Model"}
          </span>
          <input
            type="text"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            placeholder={isAzure ? "e.g. gpt-4o" : "e.g. gpt-4o, claude-sonnet-4-20250514"}
            className="mt-1 block w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-500 outline-none focus:ring-1 focus:ring-teal-400/50"
          />
        </label>

        {/* API Key */}
        <label className="block">
          <span className="text-sm text-gray-400">API Key</span>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder={maskedKey || "Paste your API key"}
            className="mt-1 block w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-500 outline-none focus:ring-1 focus:ring-teal-400/50"
          />
        </label>

        {/* Azure-specific fields */}
        {isAzure && (
          <>
            <label className="block">
              <span className="text-sm text-gray-400">Azure Endpoint</span>
              <input
                type="text"
                value={azureEndpoint}
                onChange={(e) => setAzureEndpoint(e.target.value)}
                placeholder="https://your-resource.openai.azure.com/"
                className="mt-1 block w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-500 outline-none focus:ring-1 focus:ring-teal-400/50"
              />
            </label>
            <label className="block">
              <span className="text-sm text-gray-400">API Version</span>
              <input
                type="text"
                value={azureApiVersion}
                onChange={(e) => setAzureApiVersion(e.target.value)}
                placeholder="e.g. 2024-12-01-preview"
                className="mt-1 block w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-500 outline-none focus:ring-1 focus:ring-teal-400/50"
              />
            </label>
            <label className="block">
              <span className="text-sm text-gray-400">Azure Deployment</span>
              <input
                type="text"
                value={azureDeployment}
                onChange={(e) => setAzureDeployment(e.target.value)}
                placeholder="e.g. gpt-4o"
                className="mt-1 block w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-500 outline-none focus:ring-1 focus:ring-teal-400/50"
              />
            </label>
          </>
        )}

        {/* Error message */}
        {error && (
          <p className="text-sm text-red-400">{error}</p>
        )}

        {/* Save button */}
        <button
          onClick={handleSave}
          disabled={!canSave || saving}
          className="w-full bg-teal-600 hover:bg-teal-500 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-lg px-4 py-2 text-sm font-medium transition-colors"
        >
          {saving ? "Validating..." : "Save"}
        </button>
      </div>
    </div>
  );
}
