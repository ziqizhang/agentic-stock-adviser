# Dashboard Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a React frontend that connects to the FastAPI backend via SSE, showing a chat panel and dashboard panes that populate in real time as the agent researches stocks.

**Architecture:** Vite + React + TypeScript app in `frontend/`. A single SSE connection (`useSSE` hook) receives all events and dispatches them to a Zustand store. Components read from the store and render: chat panel (collapsible, right side), stock tabs, and sub-tab panes (Chart, Fundamentals, Report). No assistant-ui for MVP — a simple custom chat component that we can swap later.

**Tech Stack:** React 18, TypeScript, Vite, Zustand, recharts (chart), react-markdown (report), Tailwind CSS (styling)

**Spec:** `docs/superpowers/specs/2026-03-29-dashboard-design.md`

**Backend API (running on port 8881):**
- `POST /chat` — `{session_id, message}` → 202
- `GET /stream/{session_id}` — SSE stream with events: `token`, `tool_start`, `tool_result`, `stock_opened`, `chart_update`, `table_update`, `report_update`

---

## File Map

```
frontend/
    package.json
    tsconfig.json
    tsconfig.app.json
    tsconfig.node.json
    vite.config.ts
    index.html
    postcss.config.js
    tailwind.config.js
    src/
        main.tsx              # React entry point
        App.tsx               # Top-level layout: Dashboard + ChatPanel
        index.css             # Tailwind base imports + dark theme globals

        store/
            types.ts          # TypeScript types (SSEEvent, StockData, ChatMessage)
            index.ts          # Zustand store (chat messages, stocks, UI state)

        stream/
            useSSE.ts         # Hook: opens EventSource, parses events, dispatches to store
            api.ts            # POST /chat helper

        chat/
            ChatPanel.tsx     # Collapsible right panel with messages + input

        dashboard/
            Dashboard.tsx     # Stock tabs bar + active stock content (or empty state)
            StockTab.tsx      # Sub-tab switcher (Chart / Fundamentals / Report) + pane content

        panes/
            ChartPane.tsx     # Recharts line chart from price data
            FundamentalsPane.tsx  # Metrics table
            ReportPane.tsx    # Markdown renderer
```

---

### Task 1: Scaffold Vite + React + TypeScript Project

**Files:**
- Create: `frontend/package.json`, `frontend/tsconfig.json`, `frontend/tsconfig.app.json`, `frontend/tsconfig.node.json`, `frontend/vite.config.ts`, `frontend/index.html`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/index.css`, `frontend/postcss.config.js`, `frontend/tailwind.config.js`

- [ ] **Step 1: Create the Vite project**

```bash
cd /home/zz/Work/github_personal/agentic-stock-adviser
npm create vite@latest frontend -- --template react-ts
```

- [ ] **Step 2: Install dependencies**

```bash
cd /home/zz/Work/github_personal/agentic-stock-adviser/frontend
npm install
npm install zustand recharts react-markdown tailwindcss @tailwindcss/vite
```

- [ ] **Step 3: Configure Tailwind**

Replace `frontend/src/index.css` with:

```css
@import "tailwindcss";
```

Update `frontend/vite.config.ts`:

```typescript
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      "/chat": "http://127.0.0.1:8881",
      "/stream": "http://127.0.0.1:8881",
      "/health": "http://127.0.0.1:8881",
    },
  },
});
```

The proxy config means the frontend dev server forwards API calls to the backend, avoiding CORS issues during development.

- [ ] **Step 4: Replace App.tsx with a placeholder**

Replace `frontend/src/App.tsx`:

```tsx
function App() {
  return (
    <div className="h-screen bg-gray-950 text-gray-200 flex items-center justify-center">
      <p className="text-gray-500">Stock Adviser Dashboard</p>
    </div>
  );
}

export default App;
```

- [ ] **Step 5: Update main.tsx**

Replace `frontend/src/main.tsx`:

```tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
```

- [ ] **Step 6: Verify it runs**

```bash
cd /home/zz/Work/github_personal/agentic-stock-adviser/frontend
npm run dev
```

Open http://localhost:5173 — should show "Stock Adviser Dashboard" on a dark background.

Kill the dev server after verifying.

- [ ] **Step 7: Add frontend to .gitignore and commit**

Add to the repo root `.gitignore` (create if needed):

```
frontend/node_modules/
frontend/dist/
```

```bash
cd /home/zz/Work/github_personal/agentic-stock-adviser
git add frontend/ .gitignore
git commit -m "feat: scaffold React frontend with Vite, Tailwind, Zustand"
```

---

### Task 2: Store Types and Zustand Store

**Files:**
- Create: `frontend/src/store/types.ts`
- Create: `frontend/src/store/index.ts`

- [ ] **Step 1: Create TypeScript types**

Create `frontend/src/store/types.ts`:

```typescript
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
}
```

- [ ] **Step 2: Create Zustand store**

Create `frontend/src/store/index.ts`:

```typescript
import { create } from "zustand";
import type { AppState, ChatMessage, StockData } from "./types";

export const useStore = create<AppState>((set, get) => ({
  // Chat state
  messages: [],
  isAgentTyping: false,

  addUserMessage: (content: string) =>
    set((s) => ({ messages: [...s.messages, { role: "user", content }] })),

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
    set((s) => ({ messages: [...s.messages, { role: "status", content }] })),

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
```

- [ ] **Step 3: Verify it compiles**

```bash
cd /home/zz/Work/github_personal/agentic-stock-adviser/frontend
npx tsc --noEmit
```

Expected: No errors.

- [ ] **Step 4: Commit**

```bash
cd /home/zz/Work/github_personal/agentic-stock-adviser
git add frontend/src/store/
git commit -m "feat: add Zustand store with chat and stock state"
```

---

### Task 3: SSE Hook and API Helper

**Files:**
- Create: `frontend/src/stream/api.ts`
- Create: `frontend/src/stream/useSSE.ts`

- [ ] **Step 1: Create API helper**

Create `frontend/src/stream/api.ts`:

```typescript
const API_BASE = "";

export async function sendChatMessage(sessionId: string, message: string): Promise<void> {
  await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message }),
  });
}
```

`API_BASE` is empty because the Vite proxy handles routing `/chat` to the backend.

- [ ] **Step 2: Create SSE hook**

Create `frontend/src/stream/useSSE.ts`:

```typescript
import { useEffect, useRef } from "react";
import { useStore } from "../store";

interface SSEEventData {
  type: string;
  data: Record<string, unknown>;
}

export function useSSE(sessionId: string) {
  const sourceRef = useRef<EventSource | null>(null);

  const appendAssistantToken = useStore((s) => s.appendAssistantToken);
  const addStatusMessage = useStore((s) => s.addStatusMessage);
  const finishAssistantMessage = useStore((s) => s.finishAssistantMessage);
  const setAgentTyping = useStore((s) => s.setAgentTyping);
  const openStock = useStore((s) => s.openStock);
  const updateChart = useStore((s) => s.updateChart);
  const updateFundamentals = useStore((s) => s.updateFundamentals);
  const updateReport = useStore((s) => s.updateReport);

  useEffect(() => {
    const source = new EventSource(`/stream/${sessionId}`);
    sourceRef.current = source;

    let wasTyping = false;

    source.onmessage = (event) => {
      let parsed: SSEEventData;
      try {
        parsed = JSON.parse(event.data);
      } catch {
        return;
      }

      const { type, data } = parsed;

      switch (type) {
        case "token":
          if (!wasTyping) {
            wasTyping = true;
          }
          appendAssistantToken(data.content as string);
          break;

        case "tool_start":
          // If we were streaming tokens, finish that message first
          if (wasTyping) {
            finishAssistantMessage();
            wasTyping = false;
          }
          setAgentTyping(true);
          addStatusMessage(data.status as string);
          break;

        case "tool_result":
          // Tool finished — agent will continue
          break;

        case "stock_opened":
          openStock(data.symbol as string, data.name as string);
          break;

        case "chart_update":
          updateChart(
            data.symbol as string,
            data.prices as number[],
            data.period as string
          );
          break;

        case "table_update":
          updateFundamentals(
            data.symbol as string,
            data.metrics as Record<string, number | null>
          );
          break;

        case "report_update":
          updateReport(data.symbol as string, data.markdown as string);
          break;
      }
    };

    source.onerror = () => {
      if (wasTyping) {
        finishAssistantMessage();
        wasTyping = false;
      }
      setAgentTyping(false);
    };

    return () => {
      source.close();
    };
  }, [sessionId]);
}
```

- [ ] **Step 3: Verify it compiles**

```bash
cd /home/zz/Work/github_personal/agentic-stock-adviser/frontend
npx tsc --noEmit
```

- [ ] **Step 4: Commit**

```bash
cd /home/zz/Work/github_personal/agentic-stock-adviser
git add frontend/src/stream/
git commit -m "feat: add SSE hook and chat API helper"
```

---

### Task 4: Chat Panel Component

**Files:**
- Create: `frontend/src/chat/ChatPanel.tsx`

- [ ] **Step 1: Create chat panel**

Create `frontend/src/chat/ChatPanel.tsx`:

```tsx
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
```

- [ ] **Step 2: Verify it compiles**

```bash
cd /home/zz/Work/github_personal/agentic-stock-adviser/frontend
npx tsc --noEmit
```

- [ ] **Step 3: Commit**

```bash
cd /home/zz/Work/github_personal/agentic-stock-adviser
git add frontend/src/chat/
git commit -m "feat: add collapsible chat panel component"
```

---

### Task 5: Dashboard Panes (Chart, Fundamentals, Report)

**Files:**
- Create: `frontend/src/panes/ChartPane.tsx`
- Create: `frontend/src/panes/FundamentalsPane.tsx`
- Create: `frontend/src/panes/ReportPane.tsx`

- [ ] **Step 1: Create ChartPane**

Create `frontend/src/panes/ChartPane.tsx`:

```tsx
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface Props {
  prices: number[];
  period: string;
}

export function ChartPane({ prices, period }: Props) {
  if (prices.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        No price data yet
      </div>
    );
  }

  const data = prices.map((price, i) => ({ index: i, price }));

  return (
    <div className="h-full p-4">
      <p className="text-xs text-gray-500 mb-2">Period: {period}</p>
      <ResponsiveContainer width="100%" height="90%">
        <LineChart data={data}>
          <XAxis dataKey="index" hide />
          <YAxis
            domain={["auto", "auto"]}
            tick={{ fill: "#6b7280", fontSize: 11 }}
            width={60}
          />
          <Tooltip
            contentStyle={{
              background: "#1f2937",
              border: "1px solid #374151",
              borderRadius: 8,
              color: "#e5e7eb",
              fontSize: 12,
            }}
          />
          <Line
            type="monotone"
            dataKey="price"
            stroke="#2dd4bf"
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
```

- [ ] **Step 2: Create FundamentalsPane**

Create `frontend/src/panes/FundamentalsPane.tsx`:

```tsx
interface Props {
  metrics: Record<string, number | null>;
}

const LABELS: Record<string, string> = {
  pe_ratio: "P/E Ratio",
  forward_pe: "Forward P/E",
  eps: "EPS",
  revenue_growth: "Revenue Growth",
  profit_margin: "Profit Margin",
  debt_to_equity: "Debt/Equity",
  return_on_equity: "Return on Equity",
  dividend_yield: "Dividend Yield",
};

function formatValue(key: string, value: number | null): string {
  if (value === null || value === undefined) return "N/A";
  if (key.includes("growth") || key.includes("margin") || key.includes("return") || key.includes("yield")) {
    return `${(value * 100).toFixed(1)}%`;
  }
  if (key.includes("ratio") || key.includes("pe") || key.includes("equity")) {
    return value.toFixed(2);
  }
  return `$${value.toFixed(2)}`;
}

export function FundamentalsPane({ metrics }: Props) {
  const entries = Object.entries(metrics);

  if (entries.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        No fundamentals data yet
      </div>
    );
  }

  return (
    <div className="p-4">
      <table className="w-full">
        <tbody>
          {entries.map(([key, value]) => (
            <tr key={key} className="border-b border-gray-800">
              <td className="py-2 text-sm text-gray-400">
                {LABELS[key] || key}
              </td>
              <td className="py-2 text-sm text-gray-200 text-right font-mono">
                {formatValue(key, value)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

- [ ] **Step 3: Create ReportPane**

Create `frontend/src/panes/ReportPane.tsx`:

```tsx
import Markdown from "react-markdown";

interface Props {
  markdown: string;
}

export function ReportPane({ markdown }: Props) {
  if (!markdown) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        No report yet
      </div>
    );
  }

  return (
    <div className="p-4 prose prose-invert prose-sm max-w-none">
      <Markdown>{markdown}</Markdown>
    </div>
  );
}
```

- [ ] **Step 4: Verify all compile**

```bash
cd /home/zz/Work/github_personal/agentic-stock-adviser/frontend
npx tsc --noEmit
```

- [ ] **Step 5: Commit**

```bash
cd /home/zz/Work/github_personal/agentic-stock-adviser
git add frontend/src/panes/
git commit -m "feat: add chart, fundamentals, and report pane components"
```

---

### Task 6: Dashboard and StockTab Components

**Files:**
- Create: `frontend/src/dashboard/Dashboard.tsx`
- Create: `frontend/src/dashboard/StockTab.tsx`

- [ ] **Step 1: Create StockTab**

Create `frontend/src/dashboard/StockTab.tsx`:

```tsx
import { useStore } from "../store";
import { ChartPane } from "../panes/ChartPane";
import { FundamentalsPane } from "../panes/FundamentalsPane";
import { ReportPane } from "../panes/ReportPane";
import type { StockData } from "../store/types";

const TABS = ["chart", "fundamentals", "report"] as const;

interface Props {
  stock: StockData;
}

export function StockTab({ stock }: Props) {
  const activeSubTab = useStore((s) => s.activeSubTab);
  const setActiveSubTab = useStore((s) => s.setActiveSubTab);

  return (
    <div className="flex flex-col h-full">
      {/* Sub-tab bar */}
      <div className="flex gap-1 px-4 border-b border-gray-800">
        {TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveSubTab(tab)}
            className={`px-4 py-2 text-sm capitalize ${
              activeSubTab === tab
                ? "text-teal-400 border-b-2 border-teal-400"
                : "text-gray-500 hover:text-gray-300"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Pane content */}
      <div className="flex-1 overflow-auto">
        {activeSubTab === "chart" && (
          <ChartPane
            prices={stock.chart?.prices ?? []}
            period={stock.chart?.period ?? ""}
          />
        )}
        {activeSubTab === "fundamentals" && (
          <FundamentalsPane metrics={stock.fundamentals ?? {}} />
        )}
        {activeSubTab === "report" && (
          <ReportPane markdown={stock.report ?? ""} />
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create Dashboard**

Create `frontend/src/dashboard/Dashboard.tsx`:

```tsx
import { useStore } from "../store";
import { StockTab } from "./StockTab";

export function Dashboard() {
  const stocks = useStore((s) => s.stocks);
  const activeStock = useStore((s) => s.activeStock);
  const setActiveStock = useStore((s) => s.setActiveStock);
  const closeStock = useStore((s) => s.closeStock);

  const stockList = Object.values(stocks);

  // Empty state
  if (stockList.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-500 text-lg">Stock Adviser</p>
          <p className="text-gray-600 text-sm mt-2">
            Ask the agent about any stock to get started
          </p>
        </div>
      </div>
    );
  }

  const currentStock = activeStock ? stocks[activeStock] : null;

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Stock tabs bar */}
      <div className="flex gap-1 px-2 pt-2 bg-gray-900 border-b border-gray-800">
        {stockList.map((stock) => (
          <div
            key={stock.symbol}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-t-lg text-sm cursor-pointer ${
              activeStock === stock.symbol
                ? "bg-gray-950 text-teal-400"
                : "bg-gray-800 text-gray-400 hover:bg-gray-750"
            }`}
            onClick={() => setActiveStock(stock.symbol)}
          >
            <span>{stock.symbol}</span>
            <button
              onClick={(e) => {
                e.stopPropagation();
                closeStock(stock.symbol);
              }}
              className="text-gray-500 hover:text-gray-300 text-xs"
            >
              &times;
            </button>
          </div>
        ))}
      </div>

      {/* Active stock content */}
      {currentStock ? (
        <StockTab stock={currentStock} />
      ) : (
        <div className="flex-1 flex items-center justify-center text-gray-500">
          Select a stock tab
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Verify it compiles**

```bash
cd /home/zz/Work/github_personal/agentic-stock-adviser/frontend
npx tsc --noEmit
```

- [ ] **Step 4: Commit**

```bash
cd /home/zz/Work/github_personal/agentic-stock-adviser
git add frontend/src/dashboard/
git commit -m "feat: add dashboard with stock tabs and sub-tab routing"
```

---

### Task 7: Wire Everything Together in App.tsx

**Files:**
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Update App.tsx to compose all components**

Replace `frontend/src/App.tsx`:

```tsx
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
```

- [ ] **Step 2: Verify it compiles**

```bash
cd /home/zz/Work/github_personal/agentic-stock-adviser/frontend
npx tsc --noEmit
```

- [ ] **Step 3: Start both backend and frontend, verify full stack**

Terminal 1 (backend):
```bash
cd /home/zz/Work/github_personal/agentic-stock-adviser
make serve
```

Terminal 2 (frontend):
```bash
cd /home/zz/Work/github_personal/agentic-stock-adviser/frontend
npm run dev
```

Open http://localhost:5173. Verify:
- Dark background with "Stock Adviser" placeholder in center
- Chat panel open on right with "Ask me about any stock to get started"
- Type "What is the price of AAPL?" and send
- Should see status messages and agent response stream in
- An "AAPL" tab should appear on the left
- Sub-tabs (Chart / Fundamentals / Report) should show data

- [ ] **Step 4: Commit**

```bash
cd /home/zz/Work/github_personal/agentic-stock-adviser
git add frontend/src/App.tsx
git commit -m "feat: wire up dashboard, chat, and SSE in App.tsx"
```

---

### Task 8: Makefile Targets for Frontend

**Files:**
- Modify: `Makefile`

- [ ] **Step 1: Add frontend targets to Makefile**

Add before the `clean` target in the Makefile:

```makefile
# Install frontend dependencies
frontend-install:
	cd frontend && npm install

# Run frontend dev server
frontend-dev:
	cd frontend && npm run dev

# Run both backend and frontend (requires two terminals)
dev:
	@echo "Start in two terminals:"
	@echo "  Terminal 1: make serve"
	@echo "  Terminal 2: make frontend-dev"
```

Add `frontend-install frontend-dev dev` to the `.PHONY` list.

- [ ] **Step 2: Commit**

```bash
cd /home/zz/Work/github_personal/agentic-stock-adviser
git add Makefile
git commit -m "chore: add frontend Makefile targets"
```

---

### Task 9: Playwright E2E Test

**Files:**
- Create: `frontend/e2e/dashboard.spec.ts`
- Modify: `frontend/package.json` (add playwright)

- [ ] **Step 1: Install Playwright**

```bash
cd /home/zz/Work/github_personal/agentic-stock-adviser/frontend
npm install -D @playwright/test
npx playwright install chromium
```

- [ ] **Step 2: Create Playwright config**

Create `frontend/playwright.config.ts`:

```typescript
import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 60000,
  use: {
    baseURL: "http://localhost:5173",
    headless: true,
  },
  webServer: {
    command: "npm run dev",
    port: 5173,
    reuseExistingServer: true,
  },
});
```

- [ ] **Step 3: Create E2E test**

Create `frontend/e2e/dashboard.spec.ts`:

```typescript
import { test, expect } from "@playwright/test";

test.describe("Dashboard", () => {
  test("shows empty state on load", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("Stock Adviser")).toBeVisible();
    await expect(
      page.getByText("Ask the agent about any stock to get started")
    ).toBeVisible();
  });

  test("chat panel is visible with placeholder", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("Agent")).toBeVisible();
    await expect(
      page.getByPlaceholder("Ask about a stock...")
    ).toBeVisible();
  });

  test("can type and send a message", async ({ page }) => {
    await page.goto("/");
    const input = page.getByPlaceholder("Ask about a stock...");
    await input.fill("What is the price of AAPL?");
    await page.getByRole("button", { name: "Send" }).click();

    // User message should appear in chat
    await expect(
      page.getByText("What is the price of AAPL?")
    ).toBeVisible();

    // Input should be cleared
    await expect(input).toHaveValue("");
  });

  test("chat panel collapses and expands", async ({ page }) => {
    await page.goto("/");

    // Close chat
    await page.getByText("»").click();
    await expect(
      page.getByPlaceholder("Ask about a stock...")
    ).not.toBeVisible();

    // Reopen chat
    await page.getByText("«").click();
    await expect(
      page.getByPlaceholder("Ask about a stock...")
    ).toBeVisible();
  });

  test("full flow: send message, see agent response and stock tab", async ({
    page,
  }) => {
    // This test requires the backend to be running on port 8881
    // Skip if backend is not available
    test.skip(
      !(await fetch("http://127.0.0.1:8881/health")
        .then((r) => r.ok)
        .catch(() => false)),
      "Backend not running on port 8881"
    );

    await page.goto("/");
    const input = page.getByPlaceholder("Ask about a stock...");
    await input.fill("What is the price of AAPL?");
    await page.getByRole("button", { name: "Send" }).click();

    // Wait for agent to respond (up to 30s)
    await expect(page.locator('[class*="bg-gray-800/50"]').first()).toBeVisible(
      { timeout: 30000 }
    );

    // A stock tab should appear
    await expect(page.getByText("AAPL")).toBeVisible({ timeout: 30000 });
  });
});
```

- [ ] **Step 4: Run the UI-only tests (no backend needed)**

```bash
cd /home/zz/Work/github_personal/agentic-stock-adviser/frontend
npx playwright test --grep "empty state|chat panel|type and send|collapses"
```

Expected: 4 tests pass (these don't need the backend).

- [ ] **Step 5: Commit**

```bash
cd /home/zz/Work/github_personal/agentic-stock-adviser
git add frontend/e2e/ frontend/playwright.config.ts frontend/package.json frontend/package-lock.json
git commit -m "feat: add Playwright e2e tests for dashboard"
```

---

### Task 10: Update AGENTS.md

**Files:**
- Modify: `AGENTS.md`

- [ ] **Step 1: Add frontend to AGENTS.md**

Add a `## Frontend` section after the existing module map:

```markdown
## Frontend

- Stack: React + TypeScript + Vite + Tailwind CSS
- Location: `frontend/`
- Dev server: `make frontend-dev` (port 5173, proxies API to backend)
- E2E tests: `cd frontend && npx playwright test`
- Key modules:
  - `store/` — Zustand store (chat messages, stock data, UI state)
  - `stream/useSSE.ts` — Single SSE connection, dispatches events to store
  - `stream/api.ts` — POST /chat helper
  - `chat/ChatPanel.tsx` — Collapsible right panel
  - `dashboard/Dashboard.tsx` — Stock tabs + empty state
  - `dashboard/StockTab.tsx` — Sub-tab routing (Chart/Fundamentals/Report)
  - `panes/` — ChartPane (recharts), FundamentalsPane (table), ReportPane (markdown)
```

- [ ] **Step 2: Commit**

```bash
cd /home/zz/Work/github_personal/agentic-stock-adviser
git add AGENTS.md
git commit -m "chore: add frontend module map to AGENTS.md"
```
