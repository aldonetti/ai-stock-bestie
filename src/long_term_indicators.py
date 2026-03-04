"""Investment-focused technical indicator calculations (daily granularity)."""

from datetime import date
from typing import Dict, Optional

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Individual indicator helpers
# ---------------------------------------------------------------------------

def _sma(prices: np.ndarray, period: int) -> Optional[float]:
    if len(prices) < period:
        return None
    return float(np.mean(prices[-period:]))


def _ema(prices: np.ndarray, period: int) -> Optional[float]:
    if len(prices) < period:
        return None
    alpha = 2.0 / (period + 1.0)
    ema = float(np.mean(prices[:period]))
    for p in prices[period:]:
        ema = alpha * float(p) + (1 - alpha) * ema
    return ema


def _rsi(prices: np.ndarray, period: int = 14) -> Optional[float]:
    if len(prices) < period + 1:
        return None
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)
    avg_gain = float(np.mean(gains[:period]))
    avg_loss = float(np.mean(losses[:period]))
    if avg_loss < 1e-10:
        avg_loss = 1e-10
    alpha = 1.0 / period
    for g, l in zip(gains[period:], losses[period:]):
        avg_gain = alpha * g + (1 - alpha) * avg_gain
        avg_loss = alpha * l + (1 - alpha) * avg_loss
    if avg_loss < 1e-10:
        return 100.0
    rs = avg_gain / avg_loss
    return float(100 - 100 / (1 + rs))


def _macd(prices: np.ndarray, fast: int = 12, slow: int = 26, signal_p: int = 9):
    """Return (macd_val, signal_val, histogram_val) or (None, None, None)."""
    if len(prices) < slow + signal_p:
        return None, None, None
    ema_f = _ema_series(prices, fast)
    ema_s = _ema_series(prices, slow)
    if ema_f is None or ema_s is None:
        return None, None, None
    macd_line = ema_f - ema_s
    signal_line = _ema_series(macd_line, signal_p)
    if signal_line is None:
        return None, None, None
    hist = macd_line - signal_line
    return float(macd_line[-1]), float(signal_line[-1]), float(hist[-1])


def _ema_series(prices: np.ndarray, period: int) -> Optional[np.ndarray]:
    if len(prices) < period:
        return None
    alpha = 2.0 / (period + 1.0)
    out = np.zeros(len(prices))
    out[period - 1] = float(np.mean(prices[:period]))
    for i in range(period, len(prices)):
        out[i] = alpha * prices[i] + (1 - alpha) * out[i - 1]
    # Zero-fill before start is fine; callers only use last value or the series
    return out


def _bollinger(prices: np.ndarray, period: int = 20, std_mult: float = 2.0):
    """Return (upper, lower, position) or (None, None, None)."""
    if len(prices) < period:
        period = len(prices)
    if period < 2:
        return None, None, None
    window = prices[-period:]
    ma = float(np.mean(window))
    std = float(np.std(window, ddof=0))
    if std < 1e-10:
        return None, None, None
    upper = ma + std_mult * std
    lower = ma - std_mult * std
    pos = (float(prices[-1]) - lower) / (upper - lower) if (upper - lower) > 0 else 0.5
    return float(upper), float(lower), float(pos)


def _atr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> Optional[float]:
    if len(closes) < period + 1:
        return None
    tr = np.maximum(
        highs[1:] - lows[1:],
        np.maximum(
            np.abs(highs[1:] - closes[:-1]),
            np.abs(lows[1:] - closes[:-1]),
        ),
    )
    if len(tr) < period:
        return None
    return float(np.mean(tr[-period:]))


def _return_pct(prices: np.ndarray, lookback_days: int) -> Optional[float]:
    if len(prices) < lookback_days + 1:
        return None
    start_price = float(prices[-lookback_days - 1])
    end_price = float(prices[-1])
    if start_price <= 0:
        return None
    return (end_price - start_price) / start_price * 100.0


def _ytd_return(df: pd.DataFrame) -> Optional[float]:
    """Compute YTD return based on last close of previous year vs current price."""
    current_year = date.today().year
    prev_year_data = df[df.index.year == current_year - 1]
    if prev_year_data.empty:
        return None
    start_price = float(prev_year_data["Close"].iloc[-1])
    end_price = float(df["Close"].iloc[-1])
    if start_price <= 0:
        return None
    return (end_price - start_price) / start_price * 100.0


# ---------------------------------------------------------------------------
# Main public function
# ---------------------------------------------------------------------------

def calculate_investment_indicators(ticker: str, df: pd.DataFrame) -> Optional[Dict]:
    """
    Compute all investment indicators for a stock.

    Args:
        ticker: Stock ticker symbol (for context only)
        df: DataFrame with OHLCV columns and DatetimeIndex (daily)

    Returns:
        Dict of indicators, or None if insufficient data
    """
    if df is None or df.empty or len(df) < 20:
        return None

    required = ["Open", "High", "Low", "Close", "Volume"]
    if not all(c in df.columns for c in required):
        return None

    closes = df["Close"].values.astype(float)
    highs = df["High"].values.astype(float)
    lows = df["Low"].values.astype(float)
    volumes = df["Volume"].values.astype(float)

    current_price = float(closes[-1])
    if current_price <= 0:
        return None

    # --- Moving averages & crossover signals ---
    sma_50 = _sma(closes, 50)
    sma_200 = _sma(closes, 200)
    ema_20 = _ema(closes, 20)
    ema_50 = _ema(closes, 50)

    golden_cross: Optional[bool] = None
    if sma_50 is not None and sma_200 is not None:
        golden_cross = sma_50 > sma_200

    # --- RSI ---
    rsi = _rsi(closes, 14)

    # --- MACD ---
    macd_val, macd_signal, macd_hist = _macd(closes)

    # --- Bollinger Bands ---
    bb_upper, bb_lower, bb_position = _bollinger(closes, 20)

    # --- ATR (volatility) ---
    atr = _atr(highs, lows, closes, 14)
    atr_pct = (atr / current_price * 100) if atr is not None and current_price > 0 else None

    # --- 52-week high/low ---
    trading_days_per_year = 252
    lookback = min(trading_days_per_year, len(closes))
    week52_high = float(np.max(closes[-lookback:]))
    week52_low = float(np.min(closes[-lookback:]))
    dist_from_high_pct = (current_price - week52_high) / week52_high * 100
    dist_from_low_pct = (current_price - week52_low) / week52_low * 100

    # --- Returns ---
    ret_1m = _return_pct(closes, 21)
    ret_3m = _return_pct(closes, 63)
    ret_6m = _return_pct(closes, 126)
    ret_1y = _return_pct(closes, 252)
    ret_ytd = _ytd_return(df)

    # --- Volume trend ---
    vol_avg_20 = float(np.mean(volumes[-20:])) if len(volumes) >= 20 else None
    vol_avg_50 = float(np.mean(volumes[-50:])) if len(volumes) >= 50 else None
    vol_trend: Optional[float] = None
    if vol_avg_20 is not None and vol_avg_50 is not None and vol_avg_50 > 0:
        vol_trend = vol_avg_20 / vol_avg_50  # >1 = increasing volume

    # --- Composite trend score (-1 to +1) ---
    trend_score = _compute_trend_score(
        current_price=current_price,
        sma_50=sma_50,
        sma_200=sma_200,
        ema_20=ema_20,
        ema_50=ema_50,
        rsi=rsi,
        macd_hist=macd_hist,
        bb_position=bb_position,
        ret_1m=ret_1m,
        vol_trend=vol_trend,
    )

    return {
        "ticker": ticker.upper(),
        "current_price": current_price,
        "data_points": len(df),
        # Moving averages
        "sma_50": sma_50,
        "sma_200": sma_200,
        "ema_20": ema_20,
        "ema_50": ema_50,
        "golden_cross": golden_cross,
        # RSI
        "rsi": rsi,
        # MACD
        "macd": macd_val,
        "macd_signal": macd_signal,
        "macd_histogram": macd_hist,
        # Bollinger Bands
        "bb_upper": bb_upper,
        "bb_lower": bb_lower,
        "bb_position": bb_position,
        # ATR / Volatility
        "atr": atr,
        "atr_pct": atr_pct,
        # 52-week levels
        "week52_high": week52_high,
        "week52_low": week52_low,
        "dist_from_52h_pct": dist_from_high_pct,
        "dist_from_52l_pct": dist_from_low_pct,
        # Returns
        "return_1m": ret_1m,
        "return_3m": ret_3m,
        "return_6m": ret_6m,
        "return_1y": ret_1y,
        "return_ytd": ret_ytd,
        # Volume
        "volume_avg_20d": vol_avg_20,
        "volume_avg_50d": vol_avg_50,
        "volume_trend": vol_trend,
        # Composite
        "trend_score": trend_score,
    }


def _compute_trend_score(
    current_price: float,
    sma_50: Optional[float],
    sma_200: Optional[float],
    ema_20: Optional[float],
    ema_50: Optional[float],
    rsi: Optional[float],
    macd_hist: Optional[float],
    bb_position: Optional[float],
    ret_1m: Optional[float],
    vol_trend: Optional[float],
) -> float:
    """
    Composite trend score from -1 (strong bear) to +1 (strong bull).

    Each signal contributes equally; unavailable signals are skipped.
    """
    signals = []

    # Price vs SMA 50
    if sma_50 is not None and sma_50 > 0:
        signals.append(1.0 if current_price > sma_50 else -1.0)

    # Price vs SMA 200
    if sma_200 is not None and sma_200 > 0:
        signals.append(1.0 if current_price > sma_200 else -1.0)

    # EMA 20 vs EMA 50
    if ema_20 is not None and ema_50 is not None:
        signals.append(1.0 if ema_20 > ema_50 else -1.0)

    # RSI — neutral zone 40-60, bullish > 60, bearish < 40
    if rsi is not None:
        if rsi > 60:
            signals.append(0.5)
        elif rsi < 40:
            signals.append(-0.5)
        else:
            signals.append(0.0)

    # MACD histogram direction
    if macd_hist is not None:
        signals.append(1.0 if macd_hist > 0 else -1.0)

    # Bollinger position: <0.3 oversold, >0.7 overbought
    if bb_position is not None:
        if bb_position > 0.7:
            signals.append(0.5)
        elif bb_position < 0.3:
            signals.append(-0.5)
        else:
            signals.append(0.0)

    # 1M return
    if ret_1m is not None:
        signals.append(1.0 if ret_1m > 0 else -1.0)

    # Volume trend: rising volume with positive momentum is bullish
    if vol_trend is not None:
        signals.append(0.5 if vol_trend > 1.1 else -0.5 if vol_trend < 0.9 else 0.0)

    if not signals:
        return 0.0
    return float(np.clip(np.mean(signals), -1.0, 1.0))
