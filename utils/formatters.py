"""Formatting utilities."""

from typing import Union


def format_price(price: float, decimals: int = 2) -> str:
    """
    Format price with currency symbol.

    Args:
        price: Price value
        decimals: Number of decimal places

    Returns:
        Formatted price string
    """
    return f"${price:,.{decimals}f}"


def format_percentage(value: float, decimals: int = 2, show_sign: bool = True) -> str:
    """
    Format percentage value.

    Args:
        value: Percentage value
        decimals: Number of decimal places
        show_sign: Whether to show + sign for positive values

    Returns:
        Formatted percentage string
    """
    sign = "+" if show_sign and value >= 0 else ""
    return f"{sign}{value:,.{decimals}f}%"


def format_volume(volume: Union[int, float]) -> str:
    """
    Format volume with appropriate units.

    Args:
        volume: Volume value

    Returns:
        Formatted volume string
    """
    if volume < 0:
        return "0"
    if volume >= 1_000_000_000:
        return f"{volume / 1_000_000_000:.2f}B"
    elif volume >= 1_000_000:
        return f"{volume / 1_000_000:.2f}M"
    elif volume >= 1_000:
        return f"{volume / 1_000:.2f}K"
    else:
        return f"{int(volume)}"
