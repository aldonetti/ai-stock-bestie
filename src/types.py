"""Type definitions for the stock analysis application."""

from typing import Optional, TypedDict


class StockInsights(TypedDict, total=False):
    """Type definition for stock analysis insights."""

    current_price: float
    price_change: float
    price_change_pct: float
    rolling_avg: float
    ema_short: Optional[float]
    ema_long: Optional[float]
    rsi: Optional[float]
    macd: Optional[float]
    signal: Optional[float]
    histogram: Optional[float]
    bollinger_upper: Optional[float]
    bollinger_lower: Optional[float]
    bb_position: Optional[float]
    support: Optional[float]
    resistance: Optional[float]
    vwap: Optional[float]
    volume_ratio: Optional[float]
    market_correlation: Optional[float]
    timestamp: str
    market_open_duration: float
