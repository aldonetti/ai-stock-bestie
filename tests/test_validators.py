"""Tests for validation utilities."""

import pandas as pd

from utils.validators import validate_price_data, validate_ticker


class TestValidateTicker:
    """Test ticker validation."""

    def test_valid_ticker(self):
        """Test valid ticker symbols."""
        assert validate_ticker("AAPL") is True
        assert validate_ticker("GOOGL") is True
        assert validate_ticker("NVDA") is True
        assert validate_ticker("TSLA") is True
        assert validate_ticker("^DJI") is True  # Index

    def test_invalid_ticker(self):
        """Test invalid ticker symbols."""
        assert validate_ticker("") is False
        assert validate_ticker("123") is False
        assert validate_ticker("AAPL123") is False
        assert validate_ticker("too_long") is False
        assert validate_ticker("AAAAAA") is False  # Too long (6 letters)
        assert validate_ticker("A-B") is False  # Contains invalid character

    def test_case_insensitive(self):
        """Test that validation handles case."""
        assert validate_ticker("aapl") is True
        assert validate_ticker("AAPL") is True
        assert validate_ticker("AaPl") is True
        assert validate_ticker("aa") is True  # Valid 2-letter ticker


class TestValidatePriceData:
    """Test price data validation."""

    def test_valid_data(self):
        """Test valid price data."""
        data = pd.DataFrame(
            {
                "Open": [100, 101, 102],
                "High": [105, 106, 107],
                "Low": [99, 100, 101],
                "Close": [103, 104, 105],
                "Volume": [1000, 2000, 3000],
            }
        )
        assert validate_price_data(data) is True

    def test_empty_data(self):
        """Test empty DataFrame."""
        assert validate_price_data(pd.DataFrame()) is False
        assert validate_price_data(None) is False

    def test_missing_columns(self):
        """Test DataFrame with missing columns."""
        data = pd.DataFrame({"Close": [100, 101]})
        assert validate_price_data(data) is False

    def test_invalid_prices(self):
        """Test DataFrame with invalid prices."""
        data = pd.DataFrame(
            {
                "Open": [100, -1, 102],
                "High": [105, 106, 107],
                "Low": [99, 100, 101],
                "Close": [103, 104, 105],
                "Volume": [1000, 2000, 3000],
            }
        )
        assert validate_price_data(data) is False

    def test_price_consistency(self):
        """Test price consistency validation."""
        # High < Low
        data = pd.DataFrame(
            {
                "Open": [100, 101, 102],
                "High": [99, 100, 101],  # Invalid
                "Low": [105, 106, 107],
                "Close": [103, 104, 105],
                "Volume": [1000, 2000, 3000],
            }
        )
        assert validate_price_data(data) is False
