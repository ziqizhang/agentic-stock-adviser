import yfinance as yf
from langchain_core.tools import tool

from stock_adviser.models import TickerMatch, TickerSearchResult, ToolError


@tool
def search_ticker(query: str) -> TickerSearchResult | ToolError:
    """Search for a stock ticker symbol by company name or partial ticker.

    Use this when the user mentions a company name instead of a ticker symbol.

    Args:
        query: Company name or partial ticker (e.g., 'Apple', 'Tesla', 'NVID')
    """
    try:
        results = yf.Search(query, max_results=5)
        matches = [
            TickerMatch(
                symbol=q.get("symbol", ""),
                name=q.get("shortname") or q.get("longname", "Unknown"),
                exchange=q.get("exchange"),
            )
            for q in results.quotes
            if q.get("symbol")
        ]
        return TickerSearchResult(query=query, matches=matches)
    except Exception as e:
        return ToolError(error=f"Failed to search for '{query}': {e}")


search_ticker.metadata = {"status": "Looking up the ticker..."}
