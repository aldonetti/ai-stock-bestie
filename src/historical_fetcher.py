"""Cache-first daily OHLCV data fetcher for the investment analysis tool."""

from datetime import date, datetime, timedelta
from typing import Optional

import pandas as pd
import yfinance as yf

import database as db

# Map period labels to approximate number of calendar days
_PERIOD_TO_DAYS = {
    "3M": 95,
    "6M": 185,
    "1Y": 370,
    "2Y": 740,
    "5Y": 1830,
}


def period_to_dates(period: str) -> tuple:
    """
    Convert a period label or ISO date range string to (start_date, end_date).

    Args:
        period: One of '3M','6M','1Y','2Y','5Y' or 'YYYY-MM-DD:YYYY-MM-DD'

    Returns:
        Tuple of (start_date_str, end_date_str) in YYYY-MM-DD format
    """
    today = date.today()
    if period in _PERIOD_TO_DAYS:
        start = today - timedelta(days=_PERIOD_TO_DAYS[period])
        return str(start), str(today)
    if ":" in period:
        parts = period.split(":")
        return parts[0].strip(), parts[1].strip()
    # Fallback: 1 year
    start = today - timedelta(days=370)
    return str(start), str(today)


def _download_from_yfinance(ticker: str, start: str, end: str) -> Optional[pd.DataFrame]:
    """Download daily OHLCV data from yfinance for the given date range."""
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(start=start, end=end, interval="1d", actions=False, auto_adjust=False)
        if df.empty:
            return None
        required = ["Open", "High", "Low", "Close", "Volume"]
        if not all(c in df.columns for c in required):
            return None
        df = df.dropna(subset=["Close", "Open", "High", "Low"])
        df = df[(df["Close"] > 0) & (df["High"] >= df["Low"])]
        if not df.index.is_monotonic_increasing:
            df = df.sort_index()
        # Normalize index to date only (remove tz info for consistency)
        df.index = pd.DatetimeIndex([d.date() for d in df.index])
        return df if not df.empty else None
    except Exception:
        return None


def fetch_historical_data(ticker: str, period: str = "1Y") -> Optional[pd.DataFrame]:
    """
    Return daily OHLCV data for the given ticker and period.

    Uses a cache-first strategy:
    1. Determine required date range from period
    2. Check what's already in the DB
    3. Download only the missing range from yfinance
    4. Store new data in DB
    5. Return combined DataFrame from DB

    Args:
        ticker: Stock ticker symbol
        period: Period label ('3M','6M','1Y','2Y','5Y') or 'YYYY-MM-DD:YYYY-MM-DD'

    Returns:
        DataFrame with OHLCV and DatetimeIndex, or None on failure
    """
    ticker = ticker.upper()
    required_start, required_end = period_to_dates(period)

    stored_start, stored_end = db.get_stored_date_range(ticker)

    needs_download = False
    download_start = required_start
    download_end = required_end

    if stored_start is None:
        # Nothing stored — download everything
        needs_download = True
    else:
        # Check if stored range covers the required range
        if required_start < stored_start:
            needs_download = True
            download_start = required_start
            download_end = stored_start  # only fetch the missing older part
        # Always refresh the tail to pick up recent days not yet stored
        today_str = str(date.today())
        if stored_end < today_str:
            # Download from day after stored_end to today
            tail_start = str(
                (datetime.strptime(stored_end, "%Y-%m-%d") + timedelta(days=1)).date()
            )
            tail_df = _download_from_yfinance(ticker, tail_start, today_str)
            if tail_df is not None and not tail_df.empty:
                db.upsert_price_history(ticker, tail_df)

        if needs_download:
            # Also download the older gap
            gap_df = _download_from_yfinance(ticker, download_start, download_end)
            if gap_df is not None and not gap_df.empty:
                db.upsert_price_history(ticker, gap_df)

    if needs_download and stored_start is None:
        # Full download
        full_df = _download_from_yfinance(ticker, download_start, download_end)
        if full_df is None:
            return None
        db.upsert_price_history(ticker, full_df)

    return db.get_price_history(ticker, start_date=required_start, end_date=required_end)


def refresh_ticker(ticker: str, period: str = "1Y") -> Optional[pd.DataFrame]:
    """Force a full re-download for a ticker, ignoring the cache."""
    ticker = ticker.upper()
    required_start, required_end = period_to_dates(period)
    df = _download_from_yfinance(ticker, required_start, required_end)
    if df is not None and not df.empty:
        db.upsert_price_history(ticker, df)
    return db.get_price_history(ticker, start_date=required_start, end_date=required_end)
