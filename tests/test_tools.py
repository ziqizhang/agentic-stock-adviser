"""Tests for tools with mocked yfinance."""

from unittest.mock import MagicMock, patch

import pandas as pd

from stock_adviser.tools.fundamentals import get_fundamentals
from stock_adviser.tools.price import get_stock_price
from stock_adviser.tools.search import search_ticker


def _mock_history(prices=None):
    """Create a mock DataFrame for ticker.history()."""
    if prices is None:
        prices = [190.0, 192.0, 195.0]
    return pd.DataFrame({"Close": prices})


class TestGetStockPrice:
    @patch("stock_adviser.tools.price.yf.Ticker")
    def test_returns_stock_price(self, mock_ticker_cls):
        mock_ticker = MagicMock()
        mock_ticker.info = {
            "currentPrice": 195.0,
            "regularMarketChangePercent": 1.2,
            "marketCap": 3_000_000_000_000,
            "fiftyTwoWeekHigh": 200.0,
            "fiftyTwoWeekLow": 150.0,
            "fiftyDayAverage": 190.0,
            "twoHundredDayAverage": 180.0,
        }
        mock_ticker.history.return_value = _mock_history()
        mock_ticker_cls.return_value = mock_ticker
        result = get_stock_price.invoke({"symbol": "AAPL"})
        assert result["symbol"] == "AAPL"
        assert result["price"] == 195.0
        assert result["market_cap"] == 3_000_000_000_000
        assert result["history_prices"] == [190.0, 192.0, 195.0]
        assert result["history_period"] == "1mo"

    @patch("stock_adviser.tools.price.yf.Ticker")
    def test_falls_back_to_regular_market_price(self, mock_ticker_cls):
        mock_ticker = MagicMock()
        mock_ticker.info = {"regularMarketPrice": 190.0}
        mock_ticker.history.return_value = _mock_history([190.0])
        mock_ticker_cls.return_value = mock_ticker
        result = get_stock_price.invoke({"symbol": "AAPL"})
        assert result["price"] == 190.0

    @patch("stock_adviser.tools.price.yf.Ticker")
    def test_returns_error_for_missing_data(self, mock_ticker_cls):
        mock_ticker_cls.return_value.info = {}
        result = get_stock_price.invoke({"symbol": "INVALID"})
        assert "error" in result
        assert "INVALID" in result["error"]

    @patch("stock_adviser.tools.price.yf.Ticker")
    def test_returns_error_on_exception(self, mock_ticker_cls):
        mock_ticker_cls.side_effect = Exception("network error")
        result = get_stock_price.invoke({"symbol": "AAPL"})
        assert "error" in result
        assert "network error" in result["error"]


class TestGetFundamentals:
    @patch("stock_adviser.tools.fundamentals.yf.Ticker")
    def test_returns_fundamentals(self, mock_ticker_cls):
        mock_ticker_cls.return_value.info = {
            "symbol": "AAPL",
            "trailingPE": 30.5,
            "forwardPE": 28.0,
            "trailingEps": 6.5,
            "revenueGrowth": 0.08,
            "profitMargins": 0.25,
            "debtToEquity": 150.0,
            "returnOnEquity": 0.45,
            "dividendYield": 0.005,
        }
        result = get_fundamentals.invoke({"symbol": "AAPL"})
        assert result["pe_ratio"] == 30.5
        assert result["dividend_yield"] == 0.005

    @patch("stock_adviser.tools.fundamentals.yf.Ticker")
    def test_returns_error_for_unknown_ticker(self, mock_ticker_cls):
        mock_ticker_cls.return_value.info = {}
        result = get_fundamentals.invoke({"symbol": "INVALID"})
        assert "error" in result

    @patch("stock_adviser.tools.fundamentals.yf.Ticker")
    def test_returns_error_on_exception(self, mock_ticker_cls):
        mock_ticker_cls.side_effect = Exception("timeout")
        result = get_fundamentals.invoke({"symbol": "AAPL"})
        assert "error" in result
        assert "timeout" in result["error"]


class TestSearchTicker:
    @patch("stock_adviser.tools.search.yf.Search")
    def test_returns_matches(self, mock_search_cls):
        mock_search_cls.return_value.quotes = [
            {"symbol": "AAPL", "shortname": "Apple Inc.", "exchange": "NMS"},
            {"symbol": "APLE", "shortname": "Apple Hospitality REIT", "exchange": "NYQ"},
        ]
        result = search_ticker.invoke({"query": "Apple"})
        assert result["query"] == "Apple"
        assert len(result["matches"]) == 2
        assert result["matches"][0]["symbol"] == "AAPL"

    @patch("stock_adviser.tools.search.yf.Search")
    def test_skips_entries_without_symbol(self, mock_search_cls):
        mock_search_cls.return_value.quotes = [
            {"shortname": "No Symbol Co."},
            {"symbol": "AAPL", "shortname": "Apple Inc.", "exchange": "NMS"},
        ]
        result = search_ticker.invoke({"query": "Apple"})
        assert len(result["matches"]) == 1

    @patch("stock_adviser.tools.search.yf.Search")
    def test_returns_empty_on_no_results(self, mock_search_cls):
        mock_search_cls.return_value.quotes = []
        result = search_ticker.invoke({"query": "xyzxyz"})
        assert result["matches"] == []

    @patch("stock_adviser.tools.search.yf.Search")
    def test_returns_error_on_exception(self, mock_search_cls):
        mock_search_cls.side_effect = Exception("API down")
        result = search_ticker.invoke({"query": "Apple"})
        assert "error" in result
        assert "API down" in result["error"]
