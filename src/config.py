"""Configuration constants and settings for the stock analysis application."""

from typing import Final

APP_TITLE: Final[str] = "AI Stock Bestie"
DEFAULT_TICKER: Final[str] = "NVDA"
DEFAULT_ANALYSIS_INTERVAL: Final[int] = 5
DEFAULT_LLM_FREQUENCY: Final[int] = 5

DATA_PERIOD: Final[str] = "1d"
DATA_INTERVAL: Final[str] = "1m"
ROLLING_WINDOW_SIZE: Final[int] = 60
MARKET_INDEX_TICKER: Final[str] = "SPY"

RSI_PERIOD: Final[int] = 14
RSI_OVERSOLD: Final[float] = 30.0
RSI_OVERBOUGHT: Final[float] = 70.0
MACD_FAST: Final[int] = 12
MACD_SLOW: Final[int] = 26
MACD_SIGNAL: Final[int] = 9
BOLLINGER_PERIOD: Final[int] = 20
BOLLINGER_STD: Final[int] = 2
SUPPORT_RESISTANCE_PERIOD: Final[int] = 30
EMA_SHORT: Final[int] = 9
EMA_LONG: Final[int] = 21
VOLUME_MA_PERIOD: Final[int] = 20

LLM_MODEL: Final[str] = "llama3"
LLM_TEMPERATURE: Final[float] = 0.7
LLM_MAX_TOKENS: Final[int] = 350
LLM_CACHE_DURATION: Final[int] = 60

MARKET_OPEN_TIME: Final[str] = "09:30:00"

# --- Investment Mode ---
INVESTMENT_DB_PATH: Final[str] = "data/investment.db"

DEFAULT_WATCHLIST: Final[list] = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN"]
DEFAULT_INVESTMENT_PERIOD: Final[str] = "1Y"
INVESTMENT_PERIODS: Final[list] = ["3M", "6M", "1Y", "2Y", "5Y"]

# LLM providers
LLM_PROVIDER_OLLAMA: Final[str] = "Ollama (local)"
LLM_PROVIDER_OPENAI: Final[str] = "OpenAI"
LLM_PROVIDER_ANTHROPIC: Final[str] = "Anthropic"
LLM_PROVIDERS: Final[list] = [LLM_PROVIDER_OLLAMA, LLM_PROVIDER_OPENAI, LLM_PROVIDER_ANTHROPIC]

OPENAI_DEFAULT_MODEL: Final[str] = "gpt-4o-mini"
ANTHROPIC_DEFAULT_MODEL: Final[str] = "claude-3-haiku-20240307"

LLM_INVESTMENT_CACHE_HOURS: Final[int] = 24
