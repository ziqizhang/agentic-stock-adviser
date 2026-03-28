"""Tests for Pydantic data models."""

from stock_adviser.models import Fundamentals, StockPrice, TickerMatch, TickerSearchResult, ToolError


class TestToolError:
    def test_create(self):
        err = ToolError(error="something broke")
        assert err.error == "something broke"

    def test_serialise(self):
        err = ToolError(error="bad ticker")
        data = err.model_dump()
        assert data == {"error": "bad ticker"}


class TestTickerModels:
    def test_ticker_match(self):
        match = TickerMatch(symbol="AAPL", name="Apple Inc.", exchange="NMS")
        assert match.symbol == "AAPL"
        assert match.exchange == "NMS"

    def test_ticker_match_no_exchange(self):
        match = TickerMatch(symbol="AAPL", name="Apple Inc.", exchange=None)
        assert match.exchange is None

    def test_search_result(self):
        result = TickerSearchResult(
            query="Apple",
            matches=[TickerMatch(symbol="AAPL", name="Apple Inc.", exchange="NMS")],
        )
        assert result.query == "Apple"
        assert len(result.matches) == 1

    def test_search_result_empty(self):
        result = TickerSearchResult(query="xyzxyz", matches=[])
        assert result.matches == []


class TestStockPrice:
    def test_full(self):
        price = StockPrice(
            symbol="AAPL",
            price=195.0,
            change_percent=1.2,
            market_cap=3_000_000_000_000,
            fifty_two_week_high=200.0,
            fifty_two_week_low=150.0,
            fifty_day_average=190.0,
            two_hundred_day_average=180.0,
        )
        assert price.symbol == "AAPL"
        assert price.price == 195.0

    def test_nullable_fields(self):
        price = StockPrice(
            symbol="AAPL",
            price=None,
            change_percent=None,
            market_cap=None,
            fifty_two_week_high=None,
            fifty_two_week_low=None,
            fifty_day_average=None,
            two_hundred_day_average=None,
        )
        assert price.price is None


class TestFundamentals:
    def test_full(self):
        f = Fundamentals(
            symbol="AAPL",
            pe_ratio=30.5,
            forward_pe=28.0,
            eps=6.5,
            revenue_growth=0.08,
            profit_margin=0.25,
            debt_to_equity=150.0,
            return_on_equity=0.45,
            dividend_yield=0.005,
        )
        assert f.symbol == "AAPL"
        assert f.pe_ratio == 30.5

    def test_all_none(self):
        f = Fundamentals(
            symbol="AAPL",
            pe_ratio=None,
            forward_pe=None,
            eps=None,
            revenue_growth=None,
            profit_margin=None,
            debt_to_equity=None,
            return_on_equity=None,
            dividend_yield=None,
        )
        assert f.eps is None
