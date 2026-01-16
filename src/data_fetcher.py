"""Data fetching module for stock and market data."""

from typing import Optional, Tuple

import pandas as pd
import yfinance as yf


def fetch_stock_data(ticker: str) -> Optional[pd.DataFrame]:
    """Fetch stock data for a given ticker."""
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d", interval="1m", actions=False, auto_adjust=False)

        if data.empty:
            data = stock.history(period="5d", interval="1m", actions=False, auto_adjust=False)
            if not data.empty:
                today = pd.Timestamp.now().normalize()
                data = data[data.index >= today]

        if data.empty:
            return None

        required_cols = ["Open", "High", "Low", "Close", "Volume"]
        if not all(col in data.columns for col in required_cols):
            return None

        data = data.dropna(subset=["Close", "Open", "High", "Low"])
        valid_mask = (
            (data["Close"] > 0)
            & (data["Open"] > 0)
            & (data["High"] > 0)
            & (data["Low"] > 0)
            & (data["High"] >= data["Low"])
            & (data["High"] >= data["Close"])
            & (data["Low"] <= data["Close"])
            & (data["High"] >= data["Open"])
            & (data["Low"] <= data["Open"])
        )
        data = data[valid_mask]

        if not data.index.is_monotonic_increasing:
            data = data.sort_index()

        return data if not data.empty else None
    except Exception:
        return None


def fetch_market_data() -> Optional[pd.DataFrame]:
    """
    Fetch S&P 500 (SPY) market data.

    Returns:
        DataFrame with SPY data or None if error
    """
    try:
        spy = yf.Ticker("SPY")
        data = spy.history(period="1d", interval="1m", actions=False, auto_adjust=False)

        if data.empty:
            data = spy.history(period="5d", interval="1m", actions=False, auto_adjust=False)
            if not data.empty:
                today = pd.Timestamp.now().normalize()
                data = data[data.index >= today]

        if data.empty:
            return None

        required_cols = ["Open", "High", "Low", "Close", "Volume"]
        if not all(col in data.columns for col in required_cols):
            return None

        data = data.dropna(subset=["Close", "Open", "High", "Low"])
        valid_mask = (
            (data["Close"] > 0)
            & (data["Open"] > 0)
            & (data["High"] > 0)
            & (data["Low"] > 0)
            & (data["High"] >= data["Low"])
            & (data["High"] >= data["Close"])
            & (data["Low"] <= data["Close"])
            & (data["High"] >= data["Open"])
            & (data["Low"] <= data["Open"])
        )
        data = data[valid_mask]

        if not data.index.is_monotonic_increasing:
            data = data.sort_index()

        return data if not data.empty else None
    except Exception:
        return None


def get_latest_price(ticker: str) -> Optional[float]:
    """Get the latest real-time price for a ticker."""
    try:
        stock = yf.Ticker(ticker)

        try:
            recent_data = stock.history(
                period="1d", interval="1m", actions=False, auto_adjust=False
            )
            if not recent_data.empty and "Close" in recent_data.columns:
                latest_close = recent_data["Close"].iloc[-1]
                if pd.notna(latest_close) and latest_close > 0:
                    return float(latest_close)
        except Exception:
            pass

        try:
            fast_info = stock.fast_info
            price_attrs = ["lastPrice", "regularMarketPrice", "price"]
            for attr in price_attrs:
                price = getattr(fast_info, attr, None)
                if price and price > 0:
                    return float(price)
        except Exception:
            pass

        try:
            info_dict = stock.info
            if info_dict:
                price_keys = ["regularMarketPrice", "currentPrice", "previousClose", "ask", "bid"]
                for key in price_keys:
                    price = info_dict.get(key)
                    if price and price > 0:
                        return float(price)
        except Exception:
            pass

        return None
    except Exception:
        return None


def fetch_all_data(ticker: str) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """
    Fetch both stock and market data.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Tuple of (stock_data, market_data)
    """
    stock_data = fetch_stock_data(ticker)
    market_data = fetch_market_data()
    return stock_data, market_data
