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
    <div className="p-4">
      <p className="text-xs text-gray-500 mb-2">Period: {period}</p>
      <div style={{ width: "100%", height: 400 }}>
        <ResponsiveContainer>
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
    </div>
  );
}
