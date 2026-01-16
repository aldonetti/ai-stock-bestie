"""Validation utilities."""

import re

import pandas as pd


def validate_ticker(ticker: str) -> bool:
    """
    Validate stock ticker symbol.

    Args:
        ticker: Ticker symbol to validate

    Returns:
        True if valid, False otherwise
    """
    if not ticker or not isinstance(ticker, str):
        return False

    # Ticker should be 1-5 uppercase letters, optionally with ^ prefix for indices
    pattern = r"^[\^]?[A-Z]{1,5}$"
    return bool(re.match(pattern, ticker.strip().upper()))


def validate_price_data(data: pd.DataFrame) -> bool:
    """
    Validate price data DataFrame.

    Args:
        data: DataFrame to validate

    Returns:
        True if valid, False otherwise
    """
    if data is None or data.empty:
        return False

    required_columns = ["Open", "High", "Low", "Close", "Volume"]
    if not all(col in data.columns for col in required_columns):
        return False

    # Check for required columns and valid values
    for col in required_columns:
        if data[col].isna().all():
            return False
        if col == "Volume":
            if (data[col] < 0).any():
                return False
        else:
            if (data[col] <= 0).any():
                return False

    # Validate price consistency
    if not (
        (data["High"] >= data["Low"]).all()
        and (data["High"] >= data["Close"]).all()
        and (data["Low"] <= data["Close"]).all()
        and (data["High"] >= data["Open"]).all()
        and (data["Low"] <= data["Open"]).all()
    ):
        return False

    return True
