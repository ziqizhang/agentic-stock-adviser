"""Tests for tools with mocked yfinance."""

from unittest.mock import patch

from stock_adviser.models import Fundamentals, StockPrice, TickerSearchResult, ToolError
from stock_adviser.tools.fundamentals import get_fundamentals
from stock_adviser.tools.price import get_stock_price
from stock_adviser.tools.search import search_ticker


class TestGetStockPrice:
    @patch("stock_adviser.tools.price.yf.Ticker")
    def test_returns_stock_price(self, mock_ticker_cls):
        mock_ticker_cls.return_value.info = {
            "currentPrice": 195.0,
            "regularMarketChangePercent": 1.2,
            "marketCap": 3_000_000_000_000,
            "fiftyTwoWeekHigh": 200.0,
            "fiftyTwoWeekLow": 150.0,
            "fiftyDayAverage": 190.0,
            "twoHundredDayAverage": 180.0,
        }
        result = get_stock_price.invoke({"symbol": "AAPL"})
        assert isinstance(result, StockPrice)
        assert result.price == 195.0
        assert result.market_cap == 3_000_000_000_000

    @patch("stock_adviser.tools.price.yf.Ticker")
    def test_falls_back_to_regular_market_price(self, mock_ticker_cls):
        mock_ticker_cls.return_value.info = {
            "regularMarketPrice": 190.0,
        }
        result = get_stock_price.invoke({"symbol": "AAPL"})
        assert isinstance(result, StockPrice)
        assert result.price == 190.0

    @patch("stock_adviser.tools.price.yf.Ticker")
    def test_returns_error_for_missing_data(self, mock_ticker_cls):
        mock_ticker_cls.return_value.info = {}
        result = get_stock_price.invoke({"symbol": "INVALID"})
        assert isinstance(result, ToolError)
        assert "INVALID" in result.error

    @patch("stock_adviser.tools.price.yf.Ticker")
    def test_returns_error_on_exception(self, mock_ticker_cls):
        mock_ticker_cls.side_effect = Exception("network error")
        result = get_stock_price.invoke({"symbol": "AAPL"})
        assert isinstance(result, ToolError)
        assert "network error" in result.error


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
        assert isinstance(result, Fundamentals)
        assert result.pe_ratio == 30.5
        assert result.dividend_yield == 0.005

    @patch("stock_adviser.tools.fundamentals.yf.Ticker")
    def test_returns_error_for_unknown_ticker(self, mock_ticker_cls):
        mock_ticker_cls.return_value.info = {}
        result = get_fundamentals.invoke({"symbol": "INVALID"})
        assert isinstance(result, ToolError)

    @patch("stock_adviser.tools.fundamentals.yf.Ticker")
    def test_returns_error_on_exception(self, mock_ticker_cls):
        mock_ticker_cls.side_effect = Exception("timeout")
        result = get_fundamentals.invoke({"symbol": "AAPL"})
        assert isinstance(result, ToolError)
        assert "timeout" in result.error


class TestSearchTicker:
    @patch("stock_adviser.tools.search.yf.Search")
    def test_returns_matches(self, mock_search_cls):
        mock_search_cls.return_value.quotes = [
            {"symbol": "AAPL", "shortname": "Apple Inc.", "exchange": "NMS"},
            {"symbol": "APLE", "shortname": "Apple Hospitality REIT", "exchange": "NYQ"},
        ]
        result = search_ticker.invoke({"query": "Apple"})
        assert isinstance(result, TickerSearchResult)
        assert result.query == "Apple"
        assert len(result.matches) == 2
        assert result.matches[0].symbol == "AAPL"

    @patch("stock_adviser.tools.search.yf.Search")
    def test_skips_entries_without_symbol(self, mock_search_cls):
        mock_search_cls.return_value.quotes = [
            {"shortname": "No Symbol Co."},
            {"symbol": "AAPL", "shortname": "Apple Inc.", "exchange": "NMS"},
        ]
        result = search_ticker.invoke({"query": "Apple"})
        assert len(result.matches) == 1

    @patch("stock_adviser.tools.search.yf.Search")
    def test_returns_empty_on_no_results(self, mock_search_cls):
        mock_search_cls.return_value.quotes = []
        result = search_ticker.invoke({"query": "xyzxyz"})
        assert isinstance(result, TickerSearchResult)
        assert result.matches == []

    @patch("stock_adviser.tools.search.yf.Search")
    def test_returns_error_on_exception(self, mock_search_cls):
        mock_search_cls.side_effect = Exception("API down")
        result = search_ticker.invoke({"query": "Apple"})
        assert isinstance(result, ToolError)
        assert "API down" in result.error
