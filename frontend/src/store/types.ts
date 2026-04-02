export interface ChatMessage {
  role: "user" | "assistant" | "status";
  content: string;
}

export interface StockData {
  symbol: string;
  name: string;
  chart: {
    prices: number[];
    period: string;
  } | null;
  fundamentals: Record<string, number | null> | null;
  report: string | null;
}

export interface AppState {
  // Chat
  messages: ChatMessage[];
  isAgentTyping: boolean;
  addUserMessage: (content: string) => void;
  appendAssistantToken: (content: string) => void;
  addStatusMessage: (content: string) => void;
  finishAssistantMessage: () => void;
  setAgentTyping: (typing: boolean) => void;

  // Stocks
  stocks: Record<string, StockData>;
  activeStock: string | null;
  activeSubTab: "chart" | "fundamentals" | "report";
  openStock: (symbol: string, name: string) => void;
  closeStock: (symbol: string) => void;
  setActiveStock: (symbol: string) => void;
  setActiveSubTab: (tab: "chart" | "fundamentals" | "report") => void;
  updateChart: (symbol: string, prices: number[], period: string) => void;
  updateFundamentals: (symbol: string, metrics: Record<string, number | null>) => void;
  updateReport: (symbol: string, markdown: string) => void;

  // Chat panel
  chatOpen: boolean;
  toggleChat: () => void;

  // Settings
  llmConfigured: boolean;
  settingsOpen: boolean;
  setLlmConfigured: (configured: boolean) => void;
  setSettingsOpen: (open: boolean) => void;
}
