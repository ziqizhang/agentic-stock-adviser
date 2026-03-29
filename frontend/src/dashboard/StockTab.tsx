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
