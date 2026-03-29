import yfinance as yf
from langchain_core.tools import tool

from stock_adviser.models import Fundamentals, ToolError


@tool
def get_fundamentals(symbol: str) -> dict:
    """Get fundamental financial metrics for a stock: P/E ratio, EPS, revenue growth, margins, debt, and dividends.

    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT', 'NVDA')
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        if not info or not info.get("symbol"):
            return ToolError(error=f"Ticker '{symbol}' not found or has no fundamental data").model_dump()
        return Fundamentals(
            symbol=symbol,
            pe_ratio=info.get("trailingPE"),
            forward_pe=info.get("forwardPE"),
            eps=info.get("trailingEps"),
            revenue_growth=info.get("revenueGrowth"),
            profit_margin=info.get("profitMargins"),
            debt_to_equity=info.get("debtToEquity"),
            return_on_equity=info.get("returnOnEquity"),
            dividend_yield=info.get("dividendYield"),
        ).model_dump()
    except Exception as e:
        return ToolError(error=f"Failed to fetch fundamentals for '{symbol}': {e}").model_dump()


get_fundamentals.metadata = {"status": "Pulling financial data..."}
