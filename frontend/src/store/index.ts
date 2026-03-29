import { create } from "zustand";
import type { AppState, StockData } from "./types";

export const useStore = create<AppState>((set) => ({
  // Chat state
  messages: [],
  isAgentTyping: false,

  addUserMessage: (content: string) =>
    set((s) => ({ messages: [...s.messages, { role: "user" as const, content }] })),

  appendAssistantToken: (content: string) =>
    set((s) => {
      const msgs = [...s.messages];
      const last = msgs[msgs.length - 1];
      if (last && last.role === "assistant") {
        msgs[msgs.length - 1] = { ...last, content: last.content + content };
      } else {
        msgs.push({ role: "assistant", content });
      }
      return { messages: msgs, isAgentTyping: true };
    }),

  addStatusMessage: (content: string) =>
    set((s) => ({ messages: [...s.messages, { role: "status" as const, content }] })),

  finishAssistantMessage: () => set({ isAgentTyping: false }),

  setAgentTyping: (typing: boolean) => set({ isAgentTyping: typing }),

  // Stock state
  stocks: {},
  activeStock: null,
  activeSubTab: "chart",

  openStock: (symbol: string, name: string) =>
    set((s) => {
      if (s.stocks[symbol]) return { activeStock: symbol };
      const stock: StockData = { symbol, name, chart: null, fundamentals: null, report: null };
      return { stocks: { ...s.stocks, [symbol]: stock }, activeStock: symbol };
    }),

  closeStock: (symbol: string) =>
    set((s) => {
      const { [symbol]: _, ...rest } = s.stocks;
      const keys = Object.keys(rest);
      return {
        stocks: rest,
        activeStock: s.activeStock === symbol ? (keys[0] ?? null) : s.activeStock,
      };
    }),

  setActiveStock: (symbol: string) => set({ activeStock: symbol }),

  setActiveSubTab: (tab) => set({ activeSubTab: tab }),

  updateChart: (symbol, prices, period) =>
    set((s) => {
      const stock = s.stocks[symbol];
      if (!stock) return s;
      return { stocks: { ...s.stocks, [symbol]: { ...stock, chart: { prices, period } } } };
    }),

  updateFundamentals: (symbol, metrics) =>
    set((s) => {
      const stock = s.stocks[symbol];
      if (!stock) return s;
      return { stocks: { ...s.stocks, [symbol]: { ...stock, fundamentals: metrics } } };
    }),

  updateReport: (symbol, markdown) =>
    set((s) => {
      const stock = s.stocks[symbol];
      if (!stock) return s;
      return { stocks: { ...s.stocks, [symbol]: { ...stock, report: markdown } } };
    }),

  // Chat panel
  chatOpen: true,
  toggleChat: () => set((s) => ({ chatOpen: !s.chatOpen })),
}));
