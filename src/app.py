"""Main Streamlit application for AI Stock Analysis."""

import time
from collections import deque
from typing import Any, Dict, Optional

import pandas as pd
import streamlit as st

import charts
import config as cfg
import constants
import data_fetcher
import indicators
import investment_ui
import llm_insights
import ui_components


def initialize_session_state() -> None:
    """Initialize all session state variables."""
    defaults: Dict[str, Any] = {
        "analyzing": False,
        "ticker": None,
        "stock_data": None,
        "dow_data": None,
        "rolling_window": deque(maxlen=cfg.ROLLING_WINDOW_SIZE),
        "dow_rolling_window": deque(maxlen=cfg.ROLLING_WINDOW_SIZE),
        "last_llm_response": None,
        "llm_cache_time": None,
        "daily_high": float("-inf"),
        "daily_low": float("inf"),
        "buying_momentum": 0.0,
        "selling_momentum": 0.0,
        "data_index": 0,
        "last_analysis_time": None,
        "cached_window_df": None,
        "cached_dow_window_df": None,
        "cached_window_len": 0,
        "cached_arrays": None,
        "cached_chart_figure": None,
        "last_chart_data_hash": None,
        "last_chart_update_index": -1,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if "last_progress" not in st.session_state:
        st.session_state.last_progress = None
    if "progress_start_time" not in st.session_state:
        st.session_state.progress_start_time = None


def process_stock_update() -> Optional[Dict[str, Any]]:
    """
    Process a new stock data point and calculate indicators.

    Returns:
        Dictionary of insights or None
    """
    if (
        st.session_state.stock_data is None
        or st.session_state.stock_data.empty
        or st.session_state.dow_data is None
        or st.session_state.dow_data.empty
    ):
        return None

    if st.session_state.data_index >= len(st.session_state.stock_data):
        st.session_state.data_index = 0
        if st.session_state.data_index >= len(st.session_state.stock_data):
            return None

    stock_row = st.session_state.stock_data.iloc[st.session_state.data_index]

    close_price = stock_row["Close"]
    open_price = stock_row["Open"]
    high_price = stock_row["High"]
    low_price = stock_row["Low"]

    if (
        pd.isna(close_price)
        or close_price <= 0
        or pd.isna(open_price)
        or open_price <= 0
        or pd.isna(high_price)
        or high_price <= 0
        or pd.isna(low_price)
        or low_price <= 0
        or high_price < low_price
        or high_price < close_price
        or low_price > close_price
        or high_price < open_price
        or low_price > open_price
    ):
        st.session_state.data_index += 1
        return None

    if st.session_state.data_index < len(st.session_state.dow_data):
        dow_row = st.session_state.dow_data.iloc[st.session_state.data_index]
    else:
        dow_row = st.session_state.dow_data.iloc[-1]

    st.session_state.rolling_window.append(stock_row)
    st.session_state.dow_rolling_window.append(dow_row)

    window_len = len(st.session_state.rolling_window)

    if (
        st.session_state.cached_window_len == window_len
        and st.session_state.cached_window_df is not None
    ):
        window_df = st.session_state.cached_window_df
        dow_window_df = st.session_state.cached_dow_window_df

        try:
            window_df.iloc[-1] = stock_row
            dow_window_df.iloc[-1] = dow_row
        except (IndexError, ValueError):
            window_df = pd.DataFrame(st.session_state.rolling_window)
            dow_window_df = pd.DataFrame(st.session_state.dow_rolling_window)
            st.session_state.cached_window_df = window_df
            st.session_state.cached_dow_window_df = dow_window_df
    else:
        window_df = pd.DataFrame(st.session_state.rolling_window)
        dow_window_df = pd.DataFrame(st.session_state.dow_rolling_window)
        st.session_state.cached_window_df = window_df
        st.session_state.cached_dow_window_df = dow_window_df
        st.session_state.cached_window_len = window_len

    if len(st.session_state.stock_data) > 0:
        last_row = st.session_state.stock_data.iloc[-1]
        if "Close" in last_row and pd.notna(last_row["Close"]) and last_row["Close"] > 0:
            current_price = float(last_row["Close"])
        else:
            current_price = float(close_price)
    else:
        current_price = float(close_price)

    if st.session_state.ticker and (
        st.session_state.data_index >= len(st.session_state.stock_data) - 1
        or st.session_state.data_index % 10 == 0
    ):
        latest_price = data_fetcher.get_latest_price(st.session_state.ticker)
        if latest_price is not None and latest_price > 0:
            current_price = latest_price

    if not pd.isna(high_price) and high_price > 0:
        if st.session_state.daily_high == float("-inf"):
            st.session_state.daily_high = float(high_price)
        else:
            st.session_state.daily_high = max(st.session_state.daily_high, float(high_price))

    if not pd.isna(low_price) and low_price > 0:
        if st.session_state.daily_low == float("inf"):
            st.session_state.daily_low = float(low_price)
        else:
            st.session_state.daily_low = min(st.session_state.daily_low, float(low_price))

    if window_len >= 2:
        momentum_window = min(20, window_len - 1)
        if momentum_window >= 1:
            try:
                start_idx = max(0, window_len - momentum_window - 1)
                recent_closes = [
                    float(st.session_state.rolling_window[i]["Close"])
                    for i in range(start_idx, window_len - 1)
                    if i < len(st.session_state.rolling_window)
                    and not pd.isna(st.session_state.rolling_window[i].get("Close", None))
                ]

                if len(recent_closes) >= 2:
                    deltas = [
                        recent_closes[i] - recent_closes[i - 1]
                        for i in range(1, len(recent_closes))
                    ]
                    buying_momentum = sum(d for d in deltas if d > 0)
                    selling_momentum = sum(abs(d) for d in deltas if d < 0)
                    st.session_state.buying_momentum = buying_momentum
                    st.session_state.selling_momentum = selling_momentum
                else:
                    prev_price = float(st.session_state.rolling_window[-2]["Close"])
                    curr_price = float(st.session_state.rolling_window[-1]["Close"])
                    change = curr_price - prev_price
                    st.session_state.buying_momentum = change if change > 0 else 0.0
                    st.session_state.selling_momentum = abs(change) if change < 0 else 0.0
            except (IndexError, KeyError, TypeError, ValueError):
                try:
                    prev_price = float(st.session_state.rolling_window[-2]["Close"])
                    curr_price = float(st.session_state.rolling_window[-1]["Close"])
                    change = curr_price - prev_price
                    st.session_state.buying_momentum = change if change > 0 else 0.0
                    st.session_state.selling_momentum = abs(change) if change < 0 else 0.0
                except Exception:
                    st.session_state.buying_momentum = 0.0
                    st.session_state.selling_momentum = 0.0

    try:
        insights = indicators.calculate_all_indicators(window_df, dow_window_df)
        if insights is None or not isinstance(insights, dict):
            st.session_state.data_index += 1
            return None

        insights["current_price"] = current_price

        if window_len >= 2:
            prev_price = float(st.session_state.rolling_window[-2]["Close"])
            insights["price_change"] = float(current_price - prev_price)
            insights["price_change_pct"] = (
                (insights["price_change"] / prev_price * 100) if prev_price != 0 else 0.0
            )

        insights["daily_high"] = (
            st.session_state.daily_high
            if st.session_state.daily_high != float("-inf")
            else current_price
        )
        insights["daily_low"] = (
            st.session_state.daily_low
            if st.session_state.daily_low != float("inf")
            else current_price
        )
        insights["buying_momentum"] = st.session_state.buying_momentum
        insights["selling_momentum"] = st.session_state.selling_momentum
    except Exception:
        st.session_state.data_index += 1
        return None

    st.session_state.data_index += 1
    return insights  # type: ignore[no-any-return]


def render_key_metrics(insights: Dict[str, float]) -> None:
    """Render key metrics (price, moving average) with aligned cards."""
    price_color = (
        constants.SUCCESS_LIGHT if insights["price_change_pct"] >= 0 else constants.DANGER_LIGHT
    )
    st.markdown(
        f"""
    <div class="metric-card" style="border-left: 4px solid {price_color}; background: {constants.SURFACE}; border: 1px solid {constants.BORDER_LIGHT}; border-radius: {constants.RADIUS_SM}; padding: 1.5rem; margin-bottom: 1.25rem; box-shadow: {constants.SHADOW_SM};">
        <div style="font-size: 0.75rem; color: {constants.TEXT_SECONDARY}; margin-bottom: 0.5rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
            Current Price
        </div>
        <div style="font-size: 1.75rem; font-weight: 700; color: {constants.TEXT_PRIMARY}; margin-bottom: 0.25rem;">
            ${insights['current_price']:.2f}
        </div>
        <div style="font-size: 0.875rem; color: {price_color}; font-weight: 600; margin-bottom: auto;">
            {insights['price_change_pct']:+.2f}%
        </div>
        <div class="metric-explanation" style="color: {constants.TEXT_SECONDARY}; font-size: 0.8125rem; line-height: 1.5; margin-top: auto;">
            The current trading price of the stock. Green means it's up, red means it's down.
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
    <div class="metric-card" style="border-left: 4px solid {constants.PRIMARY}; background: {constants.SURFACE}; border: 1px solid {constants.BORDER_LIGHT}; border-radius: {constants.RADIUS_SM}; padding: 1.5rem; margin-bottom: 1.25rem; box-shadow: {constants.SHADOW_SM};">
        <div style="font-size: 0.75rem; color: {constants.TEXT_SECONDARY}; margin-bottom: 0.5rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
            Moving Average
        </div>
        <div style="font-size: 1.75rem; font-weight: 700; color: {constants.TEXT_PRIMARY}; margin-bottom: auto;">
            ${insights['rolling_avg']:.2f}
        </div>
        <div class="metric-explanation" style="color: {constants.TEXT_SECONDARY}; font-size: 0.8125rem; line-height: 1.5; margin-top: auto;">
            Average price over the last 20 minutes. Helps identify price trends.
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_technical_indicators(insights: Dict[str, Any]) -> None:
    """Render technical indicators (RSI, MACD, Support/Resistance)."""
    if insights.get("rsi"):
        rsi = insights["rsi"]
        if rsi > cfg.RSI_OVERBOUGHT:
            rsi_color = constants.DANGER_LIGHT
            rsi_status = "Overbought"
            rsi_class = "status-overbought"
            rsi_explanation = "Stock may be overvalued - could indicate a potential price drop."
        elif rsi < cfg.RSI_OVERSOLD:
            rsi_color = constants.SUCCESS
            rsi_status = "Oversold"
            rsi_class = "status-oversold"
            rsi_explanation = (
                "Stock may be undervalued - could indicate a potential price increase."
            )
        else:
            rsi_color = constants.SECONDARY_LIGHT
            rsi_status = "Neutral"
            rsi_class = "status-neutral"
            rsi_explanation = "Stock is trading at normal levels - no strong buy or sell signal."

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                f"""
            <div class="metric-card" style="border-left: 4px solid {rsi_color}; background: {constants.SURFACE}; border: 1px solid {constants.BORDER_LIGHT}; border-radius: {constants.RADIUS_SM}; padding: 1.5rem; margin-bottom: 1.25rem; box-shadow: {constants.SHADOW_SM};">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <div>
                        <div style="font-size: 0.75rem; color: {constants.TEXT_SECONDARY}; margin-bottom: 0.5rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
                            RSI (Relative Strength Index)
                        </div>
                        <div style="font-size: 1.75rem; font-weight: 700; color: {constants.TEXT_PRIMARY};">
                            {rsi:.2f}
                        </div>
                    </div>
                    <span class="status-badge {rsi_class}">{rsi_status}</span>
                </div>
                <div style="margin-top: 0.5rem; margin-bottom: 0.75rem;">
                    <div style="background: {constants.BORDER_LIGHT}; height: 8px; border-radius: 4px; overflow: hidden;">
                        <div style="background: {rsi_color}; height: 100%; width: {rsi}%; transition: width 0.3s;"></div>
                    </div>
                </div>
                <div class="metric-explanation" style="color: {constants.TEXT_SECONDARY}; font-size: 0.8125rem; line-height: 1.5; margin-top: auto;">
                    {rsi_explanation} RSI measures momentum on a scale of 0-100.
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        if insights.get("macd"):
            macd_color = (
                constants.SUCCESS_LIGHT
                if insights.get("histogram", 0) > 0
                else constants.DANGER_LIGHT
            )
            macd_trend = (
                "Bullish (Upward)" if insights.get("histogram", 0) > 0 else "Bearish (Downward)"
            )
            with col2:
                st.markdown(
                    f"""
                <div class="metric-card" style="border-left: 4px solid {macd_color}; background: {constants.SURFACE}; border: 1px solid {constants.BORDER_LIGHT}; border-radius: {constants.RADIUS_SM}; padding: 1.5rem; margin-bottom: 1.25rem; box-shadow: {constants.SHADOW_SM};">
                    <div style="font-size: 0.75rem; color: {constants.TEXT_SECONDARY}; margin-bottom: 0.5rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
                        MACD (Moving Average Convergence Divergence)
                    </div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: {constants.TEXT_PRIMARY}; margin-bottom: 0.5rem;">
                        {insights['macd']:.2f}
                    </div>
                    <div style="font-size: 0.875rem; color: {constants.TEXT_SECONDARY}; margin-bottom: auto;">
                        Signal: {insights['signal']:.2f} | Histogram: <span style="color: {macd_color}; font-weight: 600;">{insights['histogram']:+.2f}</span>
                    </div>
                    <div class="metric-explanation" style="color: {constants.TEXT_SECONDARY}; font-size: 0.8125rem; line-height: 1.5; margin-top: auto;">
                        Trend: <strong style="color: {constants.TEXT_PRIMARY};">{macd_trend}</strong>. MACD shows momentum and trend direction. Positive histogram suggests upward momentum.
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

    support_resistance_col1, support_resistance_col2 = st.columns(2)
    with support_resistance_col1:
        if insights.get("support"):
            st.markdown(
                f"""
            <div class="metric-card" style="border-left: 4px solid {constants.SUCCESS}; background: {constants.SURFACE}; border: 1px solid {constants.BORDER_LIGHT}; border-radius: {constants.RADIUS_SM}; padding: 1.5rem; margin-bottom: 1.25rem; box-shadow: {constants.SHADOW_SM};">
                <div style="font-size: 0.75rem; color: {constants.TEXT_SECONDARY}; margin-bottom: 0.5rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Support Level</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: {constants.TEXT_PRIMARY}; margin-bottom: auto;">
                    ${insights['support']:.2f}
                </div>
                <div class="metric-explanation" style="color: {constants.TEXT_SECONDARY}; font-size: 0.8125rem; line-height: 1.5; margin-top: auto;">
                    Price level where the stock tends to find buying support and may bounce back up.
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )
    with support_resistance_col2:
        if insights.get("resistance"):
            st.markdown(
                f"""
            <div class="metric-card" style="border-left: 4px solid {constants.DANGER_LIGHT}; background: {constants.SURFACE}; border: 1px solid {constants.BORDER_LIGHT}; border-radius: {constants.RADIUS_SM}; padding: 1.5rem; margin-bottom: 1.25rem; box-shadow: {constants.SHADOW_SM};">
                <div style="font-size: 0.75rem; color: {constants.TEXT_SECONDARY}; margin-bottom: 0.5rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Resistance Level</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: {constants.TEXT_PRIMARY}; margin-bottom: auto;">
                    ${insights['resistance']:.2f}
                </div>
                <div class="metric-explanation" style="color: {constants.TEXT_SECONDARY}; font-size: 0.8125rem; line-height: 1.5; margin-top: auto;">
                    Price level where the stock may face selling pressure and struggle to go higher.
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )


def render_market_signals(insights: Dict[str, Any]) -> None:
    """Render market signals and daily price range."""
    if st.session_state.daily_high != float("-inf") and st.session_state.daily_low != float("inf"):
        range_pct = (
            (st.session_state.daily_high - st.session_state.daily_low) / st.session_state.daily_low
        ) * 100
        st.markdown(
            f"""
        <div class="metric-card" style="background: {constants.SURFACE}; border: 1px solid {constants.BORDER_LIGHT}; border-radius: {constants.RADIUS_SM}; padding: 1.5rem; margin-bottom: 1.25rem; box-shadow: {constants.SHADOW_SM};">
            <div style="font-size: 0.75rem; color: {constants.TEXT_SECONDARY}; margin-bottom: 0.5rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Daily Price Range</div>
            <div style="font-size: 0.95rem; color: {constants.TEXT_PRIMARY}; margin-bottom: 0.5rem;">
                High: <strong style="color: {constants.SUCCESS_LIGHT};">${st.session_state.daily_high:.2f}</strong> |
                Low: <strong style="color: {constants.DANGER_LIGHT};">${st.session_state.daily_low:.2f}</strong>
            </div>
            <div style="font-size: 0.75rem; color: {constants.TEXT_SECONDARY}; margin-bottom: auto;">
                Range: <span style="color: {constants.PRIMARY}; font-weight: 600;">{range_pct:.2f}%</span>
            </div>
            <div class="metric-explanation" style="color: {constants.TEXT_SECONDARY}; font-size: 0.8125rem; line-height: 1.5; margin-top: auto;">
                The highest and lowest prices the stock reached today. A larger range indicates higher volatility.
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )


def main() -> None:
    """Main application entry point."""
    st.set_page_config(page_title=cfg.APP_TITLE, layout="wide", initial_sidebar_state="expanded")

    initialize_session_state()

    ui_components.inject_custom_css()

    # --- Mode selector (top of sidebar) ---
    with st.sidebar:
        app_mode = st.radio(
            "App Mode",
            options=["📈 Real-Time", "📊 Investment"],
            horizontal=True,
            label_visibility="collapsed",
            key="app_mode",
        )
        st.markdown("---")

    if app_mode == "📊 Investment":
        investment_ui.render_investment_tab()
        return

    # --- Real-Time mode (existing code below) ---
    with st.sidebar:
        st.markdown("### Configuration")
        st.markdown("---")

        st.markdown(
            f"""
        <div class="explanation-card" style="margin-top: 0; margin-bottom: 1rem; color: {constants.TEXT_PRIMARY} !important;">
            <strong style="color: {constants.TEXT_PRIMARY} !important;">What is a Stock Ticker?</strong><br>
            <span style="color: {constants.TEXT_SECONDARY} !important;">A ticker symbol is a unique code (usually 1-5 letters) that identifies a company's stock.
            Examples: AAPL (Apple), GOOGL (Google), TSLA (Tesla).</span>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
        <div style="margin-bottom: 0.5rem;">
            <label style="color: {constants.TEXT_PRIMARY}; font-weight: 600; font-size: 0.9375rem; display: block; margin-bottom: 0.5rem;">
                Enter Stock Ticker
            </label>
        </div>
        """,
            unsafe_allow_html=True,
        )

        ticker_input = st.text_input(
            "Stock Ticker",
            value="",
            placeholder="e.g., NVDA, AAPL, GOOGL, TSLA (leave empty for default)",
            help="Enter a valid stock ticker symbol (1-5 letters). Leave empty to use default.",
            label_visibility="collapsed",
        )

        st.markdown("---")
        st.markdown("### Settings")

        st.markdown(
            f"""
        <div style="margin-bottom: 0.5rem;">
            <label style="color: {constants.TEXT_PRIMARY}; font-weight: 600; font-size: 0.9375rem; display: block; margin-bottom: 0.5rem;">
                Analysis Interval (seconds)
            </label>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
        <div class="explanation-card" style="margin-top: 0; margin-bottom: 0.75rem; color: {constants.TEXT_PRIMARY} !important;">
            <strong style="color: {constants.TEXT_PRIMARY} !important;">Analysis Interval:</strong> <span style="color: {constants.TEXT_SECONDARY} !important;">How frequently the app updates stock data and recalculates indicators.
            Lower values = more frequent updates (uses more resources).</span>
        </div>
        """,
            unsafe_allow_html=True,
        )

        analysis_interval = st.slider(
            "Analysis Interval",
            min_value=5,
            max_value=60,
            value=cfg.DEFAULT_ANALYSIS_INTERVAL,
            step=5,
            help="How often to update the analysis (5-60 seconds)",
            label_visibility="collapsed",
        )

        st.markdown(
            f"""
        <div style="margin-bottom: 0.5rem; margin-top: 1rem;">
            <label style="color: {constants.TEXT_PRIMARY}; font-weight: 600; font-size: 0.9375rem; display: block; margin-bottom: 0.5rem;">
                AI Insights Frequency (minutes)
            </label>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
        <div class="explanation-card" style="margin-top: 0; margin-bottom: 0.75rem; color: {constants.TEXT_PRIMARY} !important;">
            <strong style="color: {constants.TEXT_PRIMARY} !important;">AI Insights Frequency:</strong> <span style="color: {constants.TEXT_SECONDARY} !important;">How often the AI generates analysis and recommendations.
            More frequent = more insights but uses more processing power.</span>
        </div>
        """,
            unsafe_allow_html=True,
        )

        llm_trigger_minutes = st.slider(
            "AI Insights Frequency",
            min_value=1,
            max_value=10,
            value=cfg.DEFAULT_LLM_FREQUENCY,
            step=1,
            help="How often to generate AI-powered insights (1-10 minutes)",
            label_visibility="collapsed",
        )

        st.markdown("---")

        button_col1, button_col2 = st.columns(2)

        with button_col1:
            if st.button("Start Analysis", type="primary", use_container_width=True):
                ticker_to_use = (
                    ticker_input.strip().upper() if ticker_input.strip() else cfg.DEFAULT_TICKER
                )
                if ticker_to_use:
                    st.session_state.analyzing = True
                    st.session_state.ticker = ticker_to_use
                    st.session_state.data_index = 0
                    st.session_state.daily_high = float("-inf")
                    st.session_state.daily_low = float("inf")
                    st.session_state.buying_momentum = 0.0
                    st.session_state.selling_momentum = 0.0
                    st.session_state.rolling_window = deque(maxlen=cfg.ROLLING_WINDOW_SIZE)
                    st.session_state.dow_rolling_window = deque(maxlen=cfg.ROLLING_WINDOW_SIZE)
                    st.session_state.last_analysis_time = None
                    st.session_state.last_llm_response = None
                    st.session_state.llm_cache_time = None
                    st.session_state.cached_window_df = None
                    st.session_state.cached_dow_window_df = None
                    st.session_state.cached_window_len = 0
                    st.session_state.cached_arrays = None

                    with st.spinner("Fetching data..."):
                        stock_data, dow_data = data_fetcher.fetch_all_data(st.session_state.ticker)

                        if stock_data is None or stock_data.empty:
                            st.error(f"No data available for ticker {st.session_state.ticker}")
                            st.session_state.analyzing = False
                        else:
                            st.session_state.stock_data = stock_data
                            st.session_state.dow_data = dow_data
                            st.success(f"Started analyzing {st.session_state.ticker}")
                            try:
                                st.rerun()
                            except Exception:
                                pass
                else:
                    st.warning("Please enter a valid ticker symbol")

        with button_col2:
            if st.button("Stop Analysis", use_container_width=True):
                st.session_state.analyzing = False
                st.success("Analysis stopped")
                try:
                    st.rerun()
                except Exception:
                    pass

    if st.session_state.analyzing and st.session_state.ticker:
        ui_components.render_status_bar(
            st.session_state.ticker,
            analysis_interval,
            llm_trigger_minutes,
            len(st.session_state.rolling_window),
        )

        if st.session_state.stock_data is not None and len(st.session_state.stock_data) > 0:
            total_data_points = len(st.session_state.stock_data)
            current_index = st.session_state.data_index
            window_size = len(st.session_state.rolling_window)

            window_progress = min(window_size / cfg.ROLLING_WINDOW_SIZE, 1.0)
            data_progress = (
                min(current_index / total_data_points, 1.0) if total_data_points > 0 else 0.0
            )
            progress_value = (window_progress * 0.5) + (data_progress * 0.5)

            current_time = time.time()

            if window_size > 0:
                if st.session_state.progress_start_time is None:
                    st.session_state.progress_start_time = current_time

                if progress_value >= 0.95:
                    st.session_state.progress_start_time = None

                st.session_state.last_progress = progress_value

            progress_col = st.container()

            with progress_col:
                if progress_value < 1.0:
                    st.markdown(
                        f"""
                    <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem;">
                        <span class="loading-label" style="font-size: 0.875rem; color: {constants.TEXT_SECONDARY}; font-weight: 500;">Loading<span class="loading-dots"></span></span>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        "<div style='height: 24px; visibility: hidden;'></div>",
                        unsafe_allow_html=True,
                    )
                st.progress(min(progress_value, 1.0))

        st.markdown("### Price Chart")
        chart_container = st.container()
        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("---")
        metrics_col1, metrics_col2 = st.columns(2, gap="large")

        with metrics_col1:
            st.markdown("### Key Metrics")
            key_metrics_container = st.container()

        with metrics_col2:
            st.markdown("### Market Signals")
            signals_container = st.container()

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("### Technical Indicators")
        indicators_container = st.container()

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("---")
        chat_container = st.container()

        insights = process_stock_update()

        if insights:
            with chart_container:
                if len(st.session_state.rolling_window) > 1:
                    if st.session_state.cached_window_df is not None:
                        chart_df = st.session_state.cached_window_df
                    else:
                        chart_df = pd.DataFrame(list(st.session_state.rolling_window))

                    current_window_len = len(st.session_state.rolling_window)
                    window_full = current_window_len >= cfg.ROLLING_WINDOW_SIZE

                    should_update_chart = (
                        st.session_state.cached_chart_figure is None
                        or st.session_state.cached_window_len != current_window_len
                        or (window_full and st.session_state.data_index % 3 == 0)
                        or (not window_full and st.session_state.data_index % 5 == 0)
                    )

                    if should_update_chart:
                        fig = charts.create_price_chart(chart_df)
                        st.session_state.cached_chart_figure = fig
                        st.session_state.cached_window_len = current_window_len
                    else:
                        fig = st.session_state.cached_chart_figure

                    st.plotly_chart(
                        fig,
                        width="stretch",
                        key="price_chart",
                        config={
                            "displayModeBar": True,
                            "displaylogo": False,
                            "modeBarButtonsToRemove": ["pan2d", "lasso2d", "select2d"],
                            "modeBarButtonsToAdd": [],
                            "toImageButtonOptions": {
                                "format": "png",
                                "filename": "stock_chart",
                                "height": 600,
                                "width": 1200,
                                "scale": 2,
                            },
                        },
                    )

            with key_metrics_container:
                render_key_metrics(insights)

            with signals_container:
                render_market_signals(insights)

            with indicators_container:
                render_technical_indicators(insights)

            should_trigger_llm = False
            if st.session_state.last_analysis_time is None:
                should_trigger_llm = True
                st.session_state.last_analysis_time = insights["market_open_duration"]
            else:
                time_since_last = (
                    insights["market_open_duration"] - st.session_state.last_analysis_time
                )
                if time_since_last >= llm_trigger_minutes:
                    should_trigger_llm = True
                    st.session_state.last_analysis_time = insights["market_open_duration"]

            if should_trigger_llm:
                insight_text = llm_insights.get_llm_insights(
                    insights, st.session_state.ticker, use_cache=True
                )
                if insight_text:
                    with chat_container:
                        st.markdown(
                            f"""
                        <div class="ai-analysis-container" style="background: {constants.SURFACE} !important; color: {constants.TEXT_PRIMARY} !important;">
                            <div class="ai-analysis-header">
                                <h3 class="ai-analysis-title" style="color: {constants.PRIMARY} !important;">
                                    AI Analysis
                                </h3>
                                <div class="ai-analysis-timestamp" style="color: {constants.TEXT_SECONDARY} !important;">
                                    {insights['timestamp']} • {st.session_state.ticker}
                                </div>
                            </div>
                            <div class="ai-analysis-content" style="color: {constants.TEXT_PRIMARY} !important; background: transparent !important;">{insight_text}</div>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

        if st.session_state.analyzing:
            time.sleep(min(analysis_interval, 0.1))
            try:
                st.rerun()
            except Exception:
                pass

    else:
        ui_components.render_welcome_screen()

        with st.expander("How to Use", expanded=False):
            st.markdown(
                """
            **Usage Instructions:**

            1. Enter a stock ticker symbol in the sidebar (e.g., NVDA, AAPL, GOOGL)
            2. Configure analysis settings:
               - Analysis interval: Frequency of data updates
               - AI insights frequency: Frequency of AI analysis generation
            3. Click "Start Analysis" to begin
            4. View results:
               - Real-time price charts
               - Technical indicators
               - AI-powered insights
            5. Click "Stop Analysis" when finished

            **Available Indicators:**
            - Moving Averages: 5-minute and EMA indicators
            - Bollinger Bands: Volatility and price position
            - RSI: Relative Strength Index (overbought/oversold)
            - MACD: Momentum and trend analysis
            - Support/Resistance: Key price levels
            - Volume Analysis: Trading volume patterns
            - Price Momentum: Buying vs selling pressure
            """
            )

    st.markdown("---")
    ui_components.render_disclaimer()


if __name__ == "__main__":
    main()
