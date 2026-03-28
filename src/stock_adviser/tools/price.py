import yfinance as yf
from langchain_core.tools import tool

from stock_adviser.models import StockPrice, ToolError


@tool
def get_stock_price(symbol: str) -> StockPrice | ToolError:
    """Get the current stock price, daily change, market cap, and 52-week range for a ticker.

    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT', 'NVDA')
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        if not info or info.get("regularMarketPrice") is None and info.get("currentPrice") is None:
            return ToolError(error=f"Ticker '{symbol}' not found or has no market data")
        return StockPrice(
            symbol=symbol,
            price=info.get("currentPrice") or info.get("regularMarketPrice"),
            change_percent=info.get("regularMarketChangePercent"),
            market_cap=info.get("marketCap"),
            fifty_two_week_high=info.get("fiftyTwoWeekHigh"),
            fifty_two_week_low=info.get("fiftyTwoWeekLow"),
            fifty_day_average=info.get("fiftyDayAverage"),
            two_hundred_day_average=info.get("twoHundredDayAverage"),
        )
    except Exception as e:
        return ToolError(error=f"Failed to fetch price for '{symbol}': {e}")


get_stock_price.metadata = {"status": "Fetching the latest price..."}
