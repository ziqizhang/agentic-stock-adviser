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
    return (value * 100).toFixed(1) + "%";
  }
  if (key.includes("ratio") || key.includes("pe") || key.includes("equity")) {
    return value.toFixed(2);
  }
  return "$" + value.toFixed(2);
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
