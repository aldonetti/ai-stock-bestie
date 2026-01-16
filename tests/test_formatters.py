"""Tests for formatting utilities."""

from utils.formatters import format_percentage, format_price, format_volume


class TestFormatPrice:
    """Test price formatting."""

    def test_basic_price(self):
        """Test basic price formatting."""
        assert format_price(100.50) == "$100.50"
        assert format_price(1000.99) == "$1,000.99"

    def test_decimals(self):
        """Test different decimal places."""
        assert format_price(100.1234, decimals=2) == "$100.12"
        assert format_price(100.1234, decimals=4) == "$100.1234"


class TestFormatPercentage:
    """Test percentage formatting."""

    def test_basic_percentage(self):
        """Test basic percentage formatting."""
        assert format_percentage(5.5) == "+5.50%"
        assert format_percentage(-3.2) == "-3.20%"

    def test_no_sign(self):
        """Test percentage without sign."""
        assert format_percentage(5.5, show_sign=False) == "5.50%"
        assert format_percentage(-3.2, show_sign=False) == "-3.20%"


class TestFormatVolume:
    """Test volume formatting."""

    def test_small_volume(self):
        """Test small volume values."""
        assert format_volume(500) == "500"
        assert format_volume(999) == "999"
        assert format_volume(0) == "0"

    def test_k_volume(self):
        """Test thousands."""
        assert format_volume(1500) == "1.50K"
        assert format_volume(50000) == "50.00K"

    def test_m_volume(self):
        """Test millions."""
        assert format_volume(1500000) == "1.50M"
        assert format_volume(50000000) == "50.00M"

    def test_b_volume(self):
        """Test billions."""
        assert format_volume(1500000000) == "1.50B"
        assert format_volume(50000000000) == "50.00B"
