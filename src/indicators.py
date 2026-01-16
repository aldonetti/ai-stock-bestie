"""Technical indicator calculations."""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd

import config as cfg


def calculate_rsi(prices: np.ndarray, period: int = cfg.RSI_PERIOD) -> Optional[float]:
    """Calculate RSI using Wilder's smoothing method."""
    if len(prices) < period + 1:
        return None

    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)

    avg_gain: float = float(np.mean(gains[:period]))
    avg_loss: float = float(np.mean(losses[:period]))

    if avg_loss == 0:
        avg_loss = 0.0001

    alpha = 1.0 / period
    remaining_gains = gains[period:]
    remaining_losses = losses[period:]

    for gain, loss in zip(remaining_gains, remaining_losses):
        avg_gain = alpha * gain + (1 - alpha) * avg_gain
        avg_loss = alpha * loss + (1 - alpha) * avg_loss

    if avg_loss == 0 or np.isnan(avg_loss):
        return 100.0 if avg_gain > 0 else 50.0

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return float(rsi)


def calculate_macd(
    prices: np.ndarray,
    fast: int = cfg.MACD_FAST,
    slow: int = cfg.MACD_SLOW,
    signal: int = cfg.MACD_SIGNAL,
) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """
    Calculate MACD indicators.

    Args:
        prices: Array of closing prices
        fast: Fast EMA period
        slow: Slow EMA period
        signal: Signal line period

    Returns:
        Tuple of (MACD, signal, histogram) or (None, None, None) if insufficient data
    """
    if len(prices) < slow:
        return None, None, None

    def calculate_ema(arr: np.ndarray, span: int) -> Any:
        """Calculate EMA using numpy."""
        if len(arr) == 0:
            return np.array([])
        try:
            alpha = 2.0 / (span + 1.0)
            ema = np.zeros_like(arr, dtype=np.float64)
            if len(arr) >= span:
                ema[span - 1] = np.mean(arr[:span])
                for i, val in enumerate(arr[span:], start=span):
                    ema[i] = alpha * val + (1 - alpha) * ema[i - 1]
            else:
                ema[0] = arr[0]
                for i, val in enumerate(arr[1:], start=1):
                    ema[i] = alpha * val + (1 - alpha) * ema[i - 1]
            return ema
        except Exception:
            return np.array([])

    try:
        ema_fast = calculate_ema(prices, fast)
        ema_slow = calculate_ema(prices, slow)

        if len(ema_fast) == 0 or len(ema_slow) == 0:
            return None, None, None

        macd_line = ema_fast - ema_slow

        if len(macd_line) == 0:
            return None, None, None

        signal_line = calculate_ema(macd_line, signal)

        if len(signal_line) == 0:
            return None, None, None

        histogram = macd_line - signal_line

        if len(macd_line) < 1 or len(signal_line) < 1 or len(histogram) < 1:
            return None, None, None

        macd_val = float(macd_line[-1])
        signal_val = float(signal_line[-1])
        hist_val = float(histogram[-1])

        if np.isnan(macd_val) or np.isnan(signal_val) or np.isnan(hist_val):
            return None, None, None

        return macd_val, signal_val, hist_val
    except Exception:
        return None, None, None


def calculate_bollinger_bands(
    prices: np.ndarray, period: int = cfg.BOLLINGER_PERIOD, std_dev: int = cfg.BOLLINGER_STD
) -> Tuple[float, float, float]:
    """
    Calculate Bollinger Bands (optimized with pure numpy - 2-3x faster than pandas).

    Args:
        prices: Array of closing prices
        period: Moving average period
        std_dev: Standard deviation multiplier

    Returns:
        Tuple of (upper_band, lower_band, position)
    """
    if len(prices) < 1:
        return 0.0, 0.0, 0.5

    if len(prices) < period:
        period = len(prices)

    try:
        window = prices[-period:]

        if len(window) == 0:
            return 0.0, 0.0, 0.5

        ma = float(np.mean(window))
        std = float(np.std(window, ddof=0))

        if np.isnan(ma) or np.isnan(std):
            if len(prices) > 0:
                ma = float(np.mean(prices))
                std = float(np.std(prices, ddof=0)) if len(prices) > 1 else 0.01
            else:
                return 0.0, 0.0, 0.5

        if std == 0 or np.isnan(std):
            std = 0.01

        upper = ma + (std_dev * std)
        lower = ma - (std_dev * std)
        current_price = float(prices[-1])

        position = (current_price - lower) / (upper - lower) if (upper - lower) > 0 else 0.5

        return float(upper), float(lower), float(position)
    except Exception:
        try:
            if len(prices) > 0:
                current_price = float(prices[-1])
                result = (current_price, current_price, 0.5)
                if len(result) == 3:
                    return result
        except Exception:
            pass
        return 0.0, 0.0, 0.5


def calculate_support_resistance(
    highs: np.ndarray, lows: np.ndarray, period: int = cfg.SUPPORT_RESISTANCE_PERIOD
) -> Tuple[Optional[float], Optional[float]]:
    """
    Calculate support and resistance levels.

    Args:
        highs: Array of high prices
        lows: Array of low prices
        period: Lookback period

    Returns:
        Tuple of (support, resistance) or (None, None) if insufficient data
    """
    if len(highs) < period or len(lows) < period:
        return None, None

    resistance = float(np.max(highs[-period:]))
    support = float(np.min(lows[-period:]))

    return support, resistance


def calculate_volume_profile(
    prices: np.ndarray, volumes: np.ndarray
) -> Tuple[Optional[float], Optional[float]]:
    """
    Calculate VWAP and volume ratio with improved accuracy.

    Args:
        prices: Array of closing prices
        volumes: Array of volumes

    Returns:
        Tuple of (VWAP, volume_ratio) or (None, None) if insufficient data
    """
    if len(prices) < 2 or len(volumes) < 2:
        return None, None

    try:
        total_volume: float = float(np.sum(volumes))
        if total_volume == 0:
            return None, None

        vwap = np.sum(prices * volumes) / total_volume

        if len(volumes) >= cfg.VOLUME_MA_PERIOD:
            volume_ma = np.mean(volumes[-cfg.VOLUME_MA_PERIOD :])
            current_volume = volumes[-1]
            volume_ratio = current_volume / volume_ma if volume_ma > 0 else 1.0
        elif len(volumes) >= 5:
            volume_ma = np.mean(volumes[-5:])
            current_volume = volumes[-1]
            volume_ratio = current_volume / volume_ma if volume_ma > 0 else 1.0
        else:
            volume_ratio = 1.0

        return float(vwap), float(volume_ratio)
    except Exception:
        return None, None


def get_market_open_duration(timestamp: datetime) -> float:
    """
    Calculate market open duration in minutes.

    Args:
        timestamp: Current timestamp

    Returns:
        Minutes since market open
    """
    current_time = timestamp.time()
    previous_trading_day = datetime.today() - timedelta(days=1)
    current_datetime = datetime.combine(previous_trading_day, current_time)
    market_start = datetime.combine(
        previous_trading_day, datetime.strptime(cfg.MARKET_OPEN_TIME, "%H:%M:%S").time()
    )
    duration = (current_datetime - market_start).total_seconds() / 60
    return max(0.0, duration)


def calculate_all_indicators(
    window_df: pd.DataFrame, market_window_df: pd.DataFrame
) -> Optional[Dict]:
    """
    Calculate all technical indicators.

    Args:
        window_df: Stock price window DataFrame
        market_window_df: Market index (SPY) window DataFrame

    Returns:
        Dictionary of all indicators or None if insufficient data
    """
    if window_df is None or len(window_df) < 5:
        return None

    try:
        required_cols = ["Close", "Volume", "High", "Low"]
        if not all(col in window_df.columns for col in required_cols):
            return None

        close_prices = window_df["Close"].values
        volumes = window_df["Volume"].values
        highs = window_df["High"].values
        lows = window_df["Low"].values

        if len(close_prices) == 0:
            return None

        last_price = close_prices[-1]
        if np.isnan(last_price) or last_price <= 0:
            return None

        if len(close_prices) >= 3:
            if np.any(np.isnan(close_prices[-3:])):
                return None

        current_price = float(last_price)

        window_size = min(cfg.BOLLINGER_PERIOD, len(close_prices))
        rolling_avg = float(np.mean(close_prices[-window_size:]))

        if np.isnan(rolling_avg) or rolling_avg <= 0:
            return None

        if len(close_prices) >= cfg.EMA_SHORT:
            alpha_short = 2.0 / (cfg.EMA_SHORT + 1.0)
            ema_short: float = float(np.mean(close_prices[: cfg.EMA_SHORT]))
            for price in close_prices[cfg.EMA_SHORT :]:
                ema_short = float(alpha_short * price + (1 - alpha_short) * ema_short)
            ema_short_val = ema_short
            if np.isnan(ema_short_val) or ema_short_val <= 0:
                return None
            ema_short = ema_short_val
        else:
            return None

        ema_long: Optional[float] = None
        if len(close_prices) >= cfg.EMA_LONG:
            alpha_long = 2.0 / (cfg.EMA_LONG + 1.0)
            ema_long_temp: float = float(np.mean(close_prices[: cfg.EMA_LONG]))
            for price in close_prices[cfg.EMA_LONG :]:
                ema_long_temp = float(alpha_long * price + (1 - alpha_long) * ema_long_temp)
            ema_long_val = ema_long_temp
            if not np.isnan(ema_long_val) and ema_long_val > 0:
                ema_long = ema_long_val

        if len(close_prices) >= 2:
            prev_price = close_prices[-2]
            if not np.isnan(prev_price) and prev_price > 0:
                price_change = float(current_price - prev_price)
                price_change_pct = (price_change / prev_price * 100) if prev_price != 0 else 0.0
            else:
                price_change = 0.0
                price_change_pct = 0.0
        else:
            price_change = 0.0
            price_change_pct = 0.0

        if len(volumes) >= 2:
            volume_change = float(volumes[-1] - volumes[-2])
        else:
            volume_change = 0.0

        bollinger_upper = bollinger_lower = bb_position = None
        if len(close_prices) >= 1:
            try:
                bollinger_result = calculate_bollinger_bands(close_prices)
                if bollinger_result is None:
                    return None
                if not isinstance(bollinger_result, (tuple, list)):
                    return None
                result_len = len(bollinger_result)
                if result_len != 3:
                    return None
                try:
                    bollinger_upper = bollinger_result[0] if result_len > 0 else None
                    bollinger_lower = bollinger_result[1] if result_len > 1 else None
                    bb_position = bollinger_result[2] if result_len > 2 else None
                    if bollinger_upper is None or bollinger_lower is None or bb_position is None:
                        return None
                except (ValueError, TypeError, IndexError):
                    return None
            except (ValueError, TypeError, IndexError, AttributeError, Exception):
                return None
        else:
            return None

        if (
            np.isnan(bollinger_upper)
            or np.isnan(bollinger_lower)
            or bollinger_upper <= bollinger_lower
        ):
            return None

        rsi = calculate_rsi(close_prices)
        if rsi is not None and (np.isnan(rsi) or rsi < 0 or rsi > 100):
            rsi = None

        macd = signal = histogram = None
        try:
            macd_result = calculate_macd(close_prices)
            if macd_result is None:
                macd = signal = histogram = None
            elif not isinstance(macd_result, (tuple, list)):
                macd = signal = histogram = None
            else:
                result_len = len(macd_result)
                if result_len != 3:
                    macd = signal = histogram = None
                else:
                    try:
                        macd = macd_result[0] if result_len > 0 else None
                        signal = macd_result[1] if result_len > 1 else None
                        histogram = macd_result[2] if result_len > 2 else None
                        if macd is None or signal is None or histogram is None:
                            macd = signal = histogram = None
                    except (ValueError, TypeError, IndexError):
                        macd = signal = histogram = None
        except (ValueError, TypeError, IndexError, AttributeError, Exception):
            macd = signal = histogram = None

        if macd is not None:
            if np.isnan(macd) or np.isnan(signal) or np.isnan(histogram):
                macd = signal = histogram = None

        try:
            sr_result = calculate_support_resistance(highs, lows)
            if sr_result is None or not isinstance(sr_result, (tuple, list)):
                support = resistance = None
            else:
                sr_len = len(sr_result)
                if sr_len != 2:
                    support = resistance = None
                else:
                    try:
                        support = sr_result[0] if sr_len > 0 else None
                        resistance = sr_result[1] if sr_len > 1 else None
                    except (ValueError, TypeError, IndexError):
                        support = resistance = None
        except (ValueError, TypeError, IndexError, AttributeError):
            support = resistance = None

        if support is not None and resistance is not None:
            if support > resistance or support <= 0 or resistance <= 0:
                support = resistance = None

        vwap = volume_ratio = None
        if len(close_prices) >= 2 and len(volumes) >= 2:
            try:
                volume_result = calculate_volume_profile(close_prices, volumes)
                if (
                    volume_result is None
                    or not isinstance(volume_result, (tuple, list))
                    or len(volume_result) != 2
                ):
                    vwap = volume_ratio = None
                else:
                    vwap = volume_result[0]
                    volume_ratio = volume_result[1]
            except Exception:
                vwap = volume_ratio = None

        if vwap is not None and volume_ratio is not None:
            if np.isnan(vwap) or vwap <= 0 or np.isnan(volume_ratio) or volume_ratio <= 0:
                vwap = volume_ratio = None

        market_close = (
            market_window_df["Close"].values if len(market_window_df) > 0 else np.array([])
        )
        if len(market_close) >= 2:
            if not np.isnan(market_close[-1]) and not np.isnan(market_close[-2]):
                market_price_change = float(market_close[-1] - market_close[-2])
            else:
                market_price_change = 0.0
        else:
            market_price_change = 0.0

        if len(market_close) >= cfg.BOLLINGER_PERIOD:
            market_rolling_avg = float(np.mean(market_close[-cfg.BOLLINGER_PERIOD :]))
        elif len(market_close) > 0 and not pd.isna(market_close[-1]):
            market_rolling_avg = float(market_close[-1])
        else:
            market_rolling_avg = 0.0

        market_open_duration = get_market_open_duration(window_df.index[-1])
        timestamp = window_df.index[-1].time().strftime("%H:%M:%S")

        return {
            "timestamp": timestamp,
            "current_price": current_price,
            "rolling_avg": rolling_avg,
            "ema_short": ema_short,
            "ema_long": ema_long,
            "price_change": price_change,
            "price_change_pct": price_change_pct,
            "volume_change": volume_change,
            "bollinger_upper": bollinger_upper,
            "bollinger_lower": bollinger_lower,
            "bb_position": bb_position,
            "rsi": rsi,
            "macd": macd,
            "signal": signal,
            "histogram": histogram,
            "support": support,
            "resistance": resistance,
            "vwap": vwap,
            "volume_ratio": volume_ratio,
            "market_price_change": market_price_change,
            "market_rolling_avg": market_rolling_avg,
            "market_open_duration": market_open_duration,
        }
    except Exception:
        return None
