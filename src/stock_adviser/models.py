from pydantic import BaseModel


class ToolError(BaseModel):
    error: str


class TickerMatch(BaseModel):
    symbol: str
    name: str
    exchange: str | None


class TickerSearchResult(BaseModel):
    query: str
    matches: list[TickerMatch]


class StockPrice(BaseModel):
    symbol: str
    price: float | None
    change_percent: float | None
    market_cap: int | None
    fifty_two_week_high: float | None
    fifty_two_week_low: float | None
    fifty_day_average: float | None
    two_hundred_day_average: float | None


class Fundamentals(BaseModel):
    symbol: str
    pe_ratio: float | None
    forward_pe: float | None
    eps: float | None
    revenue_growth: float | None
    profit_margin: float | None
    debt_to_equity: float | None
    return_on_equity: float | None
    dividend_yield: float | None
