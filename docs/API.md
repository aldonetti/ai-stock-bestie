# API Documentation

## Data Fetcher Module

### `fetch_stock_data(ticker: str) -> Optional[pd.DataFrame]`

Fetches stock data for a given ticker.

**Parameters:**
- `ticker` (str): Stock ticker symbol

**Returns:**
- `Optional[pd.DataFrame]`: DataFrame with OHLCV data or None if error

**Example:**
```python
from src.data_fetcher import fetch_stock_data

data = fetch_stock_data("AAPL")
```

### `fetch_market_data() -> Optional[pd.DataFrame]`

Fetches S&P 500 (SPY) market data.

**Returns:**
- `Optional[pd.DataFrame]`: DataFrame with SPY data or None if error

## Indicators Module

### `calculate_rsi(prices: np.ndarray, period: int = 14) -> Optional[float]`

Calculates Relative Strength Index.

**Parameters:**
- `prices` (np.ndarray): Array of closing prices
- `period` (int): RSI period (default: 14)

**Returns:**
- `Optional[float]`: RSI value (0-100) or None if insufficient data

### `calculate_macd(prices: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[Optional[float], Optional[float], Optional[float]]`

Calculates MACD indicators.

**Parameters:**
- `prices` (np.ndarray): Array of closing prices
- `fast` (int): Fast EMA period (default: 12)
- `slow` (int): Slow EMA period (default: 26)
- `signal` (int): Signal line period (default: 9)

**Returns:**
- `Tuple[Optional[float], Optional[float], Optional[float]]`: (MACD, Signal, Histogram)

### `calculate_bollinger_bands(prices: np.ndarray, period: int = 20, std_dev: int = 2) -> Tuple[float, float, float]`

Calculates Bollinger Bands.

**Parameters:**
- `prices` (np.ndarray): Array of closing prices
- `period` (int): Moving average period (default: 20)
- `std_dev` (int): Standard deviation multiplier (default: 2)

**Returns:**
- `Tuple[float, float, float]`: (Upper Band, Lower Band, Position)

## Charts Module

### `create_price_chart(window_df: pd.DataFrame) -> go.Figure`

Creates interactive price chart with indicators.

**Parameters:**
- `window_df` (pd.DataFrame): DataFrame with price data

**Returns:**
- `go.Figure`: Plotly figure object

## Utils Module

### `validate_ticker(ticker: str) -> bool`

Validates stock ticker symbol.

**Parameters:**
- `ticker` (str): Ticker symbol to validate

**Returns:**
- `bool`: True if valid, False otherwise

### `format_price(price: float, decimals: int = 2) -> str`

Formats price with currency symbol.

**Parameters:**
- `price` (float): Price value
- `decimals` (int): Number of decimal places

**Returns:**
- `str`: Formatted price string (e.g., "$100.50")

### `format_percentage(value: float, decimals: int = 2, show_sign: bool = True) -> str`

Formats percentage value.

**Parameters:**
- `value` (float): Percentage value
- `decimals` (int): Number of decimal places
- `show_sign` (bool): Whether to show + sign for positive values

**Returns:**
- `str`: Formatted percentage string (e.g., "+5.50%")
