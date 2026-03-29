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
