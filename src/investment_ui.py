"""Streamlit UI components for the Investment Analysis tab."""

from typing import Dict, List, Optional, Tuple

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

import config as cfg
import database as db
import historical_fetcher as hf
import investment_llm as illm
import long_term_indicators as lti


# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------

def _init_state() -> None:
    defaults = {
        "inv_period": cfg.DEFAULT_INVESTMENT_PERIOD,
        "inv_custom_start": None,
        "inv_custom_end": None,
        "inv_llm_provider": cfg.LLM_PROVIDER_OLLAMA,
        "inv_api_key": "",
        "inv_indicators": {},   # ticker -> indicators dict
        "inv_llm_results": {},  # ticker -> recommendation text
        "inv_data_loaded": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def _render_sidebar() -> Tuple[str, Optional[str]]:
    """Render investment sidebar. Returns (effective_period, api_key)."""
    st.sidebar.header("📊 Investment Watchlist")

    # --- Add ticker ---
    col1, col2 = st.sidebar.columns([3, 1])
    with col1:
        new_ticker = st.text_input("Add ticker", key="inv_new_ticker", label_visibility="collapsed",
                                   placeholder="e.g. TSLA")
    with col2:
        if st.button("➕", key="inv_add_btn"):
            if new_ticker:
                t = new_ticker.strip().upper()
                db.add_to_watchlist(t)
                st.session_state.inv_data_loaded = False
                st.rerun()

    # --- Current watchlist with remove buttons ---
    watchlist = db.get_watchlist()
    if watchlist:
        st.sidebar.markdown("**Watchlist:**")
        for t in watchlist:
            c1, c2 = st.sidebar.columns([4, 1])
            c1.write(t)
            if c2.button("✕", key=f"inv_rm_{t}"):
                db.remove_from_watchlist(t)
                st.session_state.inv_indicators.pop(t, None)
                st.session_state.inv_llm_results.pop(t, None)
                st.rerun()
    else:
        st.sidebar.info("Watchlist is empty. Add tickers above.")

    st.sidebar.markdown("---")

    # --- Period selector ---
    st.sidebar.markdown("**Analysis Period**")
    period_choice = st.sidebar.radio(
        "Period",
        options=cfg.INVESTMENT_PERIODS + ["Custom"],
        index=cfg.INVESTMENT_PERIODS.index(st.session_state.inv_period)
        if st.session_state.inv_period in cfg.INVESTMENT_PERIODS else 0,
        horizontal=True,
        label_visibility="collapsed",
        key="inv_period_radio",
    )

    effective_period = st.session_state.inv_period
    if period_choice == "Custom":
        c1, c2 = st.sidebar.columns(2)
        with c1:
            custom_start = st.date_input("Start", key="inv_custom_start_input")
        with c2:
            custom_end = st.date_input("End", key="inv_custom_end_input")
        if custom_start and custom_end and custom_start < custom_end:
            effective_period = f"{custom_start}:{custom_end}"
            st.session_state.inv_period = effective_period
    else:
        if period_choice != st.session_state.inv_period:
            st.session_state.inv_period = period_choice
            st.session_state.inv_data_loaded = False
        effective_period = period_choice

    st.sidebar.markdown("---")

    # --- LLM provider ---
    st.sidebar.markdown("**LLM Provider**")
    provider = st.sidebar.selectbox(
        "LLM Provider",
        options=cfg.LLM_PROVIDERS,
        index=cfg.LLM_PROVIDERS.index(st.session_state.inv_llm_provider)
        if st.session_state.inv_llm_provider in cfg.LLM_PROVIDERS else 0,
        key="inv_provider_select",
        label_visibility="collapsed",
    )
    st.session_state.inv_llm_provider = provider

    api_key: Optional[str] = None
    if provider != cfg.LLM_PROVIDER_OLLAMA:
        api_key = st.sidebar.text_input(
            f"{provider} API Key",
            type="password",
            value=st.session_state.inv_api_key,
            key="inv_api_key_input",
        )
        st.session_state.inv_api_key = api_key

    st.sidebar.markdown("---")

    # --- Action buttons ---
    if st.sidebar.button("🔄 Refresh Data", key="inv_refresh_btn", use_container_width=True):
        _refresh_all_data(watchlist, effective_period)

    if st.sidebar.button("🤖 Run LLM Analysis", key="inv_llm_btn", use_container_width=True):
        _run_llm_analysis(watchlist, effective_period, provider, api_key)

    return effective_period, api_key


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _load_indicators(watchlist: List[str], period: str) -> None:
    """Load indicators for all watchlist tickers (uses DB cache for OHLCV)."""
    if not watchlist:
        return

    progress = st.progress(0, text="Loading data…")
    for i, ticker in enumerate(watchlist):
        progress.progress((i + 1) / len(watchlist), text=f"Loading {ticker}…")
        # Check analysis cache first
        cached = db.get_analysis_cache(ticker, period)
        if cached:
            st.session_state.inv_indicators[ticker] = cached
            continue
        df = hf.fetch_historical_data(ticker, period)
        if df is not None and not df.empty:
            ind = lti.calculate_investment_indicators(ticker, df)
            if ind:
                db.set_analysis_cache(ticker, period, ind)
                st.session_state.inv_indicators[ticker] = ind
    progress.empty()
    st.session_state.inv_data_loaded = True


def _refresh_all_data(watchlist: List[str], period: str) -> None:
    """Force re-download and re-compute for all tickers."""
    if not watchlist:
        return
    progress = st.progress(0, text="Refreshing…")
    for i, ticker in enumerate(watchlist):
        progress.progress((i + 1) / len(watchlist), text=f"Refreshing {ticker}…")
        df = hf.refresh_ticker(ticker, period)
        if df is not None and not df.empty:
            ind = lti.calculate_investment_indicators(ticker, df)
            if ind:
                db.set_analysis_cache(ticker, period, ind)
                st.session_state.inv_indicators[ticker] = ind
    progress.empty()
    st.session_state.inv_data_loaded = True
    st.success("Data refreshed!")


def _run_llm_analysis(watchlist: List[str], period: str, provider: str, api_key: Optional[str]) -> None:
    """Run LLM analysis for all tickers that have indicators loaded."""
    if not watchlist:
        return
    if provider != cfg.LLM_PROVIDER_OLLAMA and not api_key:
        st.warning(f"Please enter a {provider} API key in the sidebar.")
        return
    progress = st.progress(0, text="Running LLM analysis…")
    for i, ticker in enumerate(watchlist):
        progress.progress((i + 1) / len(watchlist), text=f"Analyzing {ticker} with {provider}…")
        ind = st.session_state.inv_indicators.get(ticker)
        if not ind:
            continue
        # Clear cache so we get a fresh run
        db.clear_llm_cache(ticker, period, provider)
        result = illm.get_investment_analysis(
            ticker, ind, period, provider=provider, api_key=api_key, use_cache=False
        )
        if result:
            st.session_state.inv_llm_results[ticker] = result
            db.set_llm_cache(ticker, period, provider, result)
    progress.empty()
    st.success("LLM analysis complete!")


# ---------------------------------------------------------------------------
# Overview table
# ---------------------------------------------------------------------------

def _fmt_pct(val: Optional[float]) -> str:
    if val is None:
        return "—"
    sign = "+" if val > 0 else ""
    return f"{sign}{val:.1f}%"


def _fmt_float(val: Optional[float], decimals: int = 2) -> str:
    if val is None:
        return "—"
    return f"{val:.{decimals}f}"


def _trend_emoji(score: Optional[float]) -> str:
    if score is None:
        return "⚪"
    if score > 0.4:
        return "🟢"
    if score > 0.1:
        return "🟡"
    if score > -0.1:
        return "⚪"
    if score > -0.4:
        return "🟠"
    return "🔴"


def _llm_signal(text: Optional[str]) -> str:
    if not text:
        return "—"
    upper = text.upper()
    if "BUY" in upper:
        return "🟢 BUY"
    if "SELL" in upper:
        return "🔴 SELL"
    if "HOLD" in upper:
        return "🟡 HOLD"
    return "⚪ N/A"


def _render_overview_table(watchlist: List[str]) -> None:
    indicators_map: Dict = st.session_state.inv_indicators
    llm_map: Dict = st.session_state.inv_llm_results

    if not watchlist:
        st.info("Your watchlist is empty. Add tickers in the sidebar to get started.")
        return

    rows = []
    for ticker in watchlist:
        ind = indicators_map.get(ticker)
        if not ind:
            rows.append({
                "Ticker": ticker, "Price": "—", "1M": "—", "3M": "—", "6M": "—",
                "1Y": "—", "YTD": "—", "RSI": "—", "MACD": "—",
                "BB Pos": "—", "Score": "—", "Signal": "—", "LLM": "—",
            })
            continue

        rsi = ind.get("rsi")
        macd_hist = ind.get("macd_histogram")
        bb_pos = ind.get("bb_position")
        score = ind.get("trend_score")

        rows.append({
            "Ticker": ticker,
            "Price": f"${ind.get('current_price', 0):.2f}",
            "1M": _fmt_pct(ind.get("return_1m")),
            "3M": _fmt_pct(ind.get("return_3m")),
            "6M": _fmt_pct(ind.get("return_6m")),
            "1Y": _fmt_pct(ind.get("return_1y")),
            "YTD": _fmt_pct(ind.get("return_ytd")),
            "RSI": _fmt_float(rsi, 1) if rsi else "—",
            "MACD ▲▼": "▲" if (macd_hist is not None and macd_hist > 0) else "▼",
            "BB %": _fmt_float(bb_pos * 100, 0) if bb_pos is not None else "—",
            "Score": f"{score:.2f} {_trend_emoji(score)}" if score is not None else "—",
            "LLM": _llm_signal(llm_map.get(ticker)),
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Detailed metrics expander per ticker
# ---------------------------------------------------------------------------

def _render_detail_expanders(watchlist: List[str], period: str) -> None:
    indicators_map: Dict = st.session_state.inv_indicators
    llm_map: Dict = st.session_state.inv_llm_results

    for ticker in watchlist:
        ind = indicators_map.get(ticker)
        if not ind:
            continue

        with st.expander(f"📈 {ticker} — detailed view", expanded=False):
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Price", f"${ind.get('current_price', 0):.2f}")
            col2.metric("RSI (14d)", _fmt_float(ind.get("rsi"), 1))
            col3.metric("1Y Return", _fmt_pct(ind.get("return_1y")))
            col4.metric("Trend Score", _fmt_float(ind.get("trend_score"), 2))

            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Moving Averages**")
                st.write(f"SMA 50: ${_fmt_float(ind.get('sma_50'))}")
                st.write(f"SMA 200: ${_fmt_float(ind.get('sma_200'))}")
                cross = ind.get("golden_cross")
                st.write(f"MA Signal: {'🟢 Golden Cross' if cross else '🔴 Death Cross' if cross is False else '—'}")
                st.write(f"EMA 20: ${_fmt_float(ind.get('ema_20'))}")
                st.write(f"EMA 50: ${_fmt_float(ind.get('ema_50'))}")

            with c2:
                st.markdown("**52-Week Range**")
                st.write(f"High: ${_fmt_float(ind.get('week52_high'))} ({_fmt_pct(ind.get('dist_from_52h_pct'))} from current)")
                st.write(f"Low:  ${_fmt_float(ind.get('week52_low'))} ({_fmt_pct(ind.get('dist_from_52l_pct'))} from current)")
                st.markdown("**Volatility**")
                st.write(f"ATR (14d): ${_fmt_float(ind.get('atr'))} ({_fmt_float(ind.get('atr_pct'))}% of price)")

            # Chart
            df = hf.fetch_historical_data(ticker, period)
            if df is not None and not df.empty:
                _render_mini_chart(ticker, df, ind)

            # LLM recommendation
            llm_text = llm_map.get(ticker)
            if llm_text:
                st.markdown("**🤖 LLM Investment Analysis**")
                st.markdown(llm_text)
            else:
                st.caption("Run LLM Analysis from the sidebar to see AI recommendations.")


def _render_mini_chart(ticker: str, df: pd.DataFrame, ind: Dict) -> None:
    """Render a price chart with SMA50/200 overlay and volume subplot."""
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.75, 0.25],
        vertical_spacing=0.03,
    )

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        name="Price",
        increasing_line_color="#26a69a",
        decreasing_line_color="#ef5350",
        showlegend=False,
    ), row=1, col=1)

    closes = df["Close"].values
    dates = df.index

    # SMA 50
    if len(closes) >= 50:
        sma50 = pd.Series(closes).rolling(50).mean().values
        fig.add_trace(go.Scatter(x=dates, y=sma50, name="SMA 50",
                                 line=dict(color="#ff9800", width=1.5)), row=1, col=1)

    # SMA 200
    if len(closes) >= 200:
        sma200 = pd.Series(closes).rolling(200).mean().values
        fig.add_trace(go.Scatter(x=dates, y=sma200, name="SMA 200",
                                 line=dict(color="#9c27b0", width=1.5)), row=1, col=1)

    # Bollinger Bands
    bb_upper = ind.get("bb_upper")
    bb_lower = ind.get("bb_lower")
    if bb_upper and bb_lower:
        bb20_mid = pd.Series(closes).rolling(20).mean().values
        bb20_std = pd.Series(closes).rolling(20).std().values
        bb_up = bb20_mid + 2 * bb20_std
        bb_dn = bb20_mid - 2 * bb20_std
        fig.add_trace(go.Scatter(x=dates, y=bb_up, name="BB Upper",
                                 line=dict(color="#42a5f5", width=1, dash="dot"), showlegend=False), row=1, col=1)
        fig.add_trace(go.Scatter(x=dates, y=bb_dn, name="BB Lower",
                                 line=dict(color="#42a5f5", width=1, dash="dot"), fill="tonexty",
                                 fillcolor="rgba(66,165,245,0.05)", showlegend=False), row=1, col=1)

    # Volume bars
    vol_colors = ["#26a69a" if c >= o else "#ef5350"
                  for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(go.Bar(x=dates, y=df["Volume"], name="Volume",
                         marker_color=vol_colors, showlegend=False), row=2, col=1)

    fig.update_layout(
        title=f"{ticker} — {len(df)} trading days",
        xaxis_rangeslider_visible=False,
        height=420,
        margin=dict(l=0, r=0, t=35, b=0),
        legend=dict(orientation="h", y=1.02, x=0),
    )
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)

    st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Main render entry point
# ---------------------------------------------------------------------------

def render_investment_tab() -> None:
    """Render the full investment analysis tab."""
    db.init_db()
    _init_state()

    # Seed watchlist with defaults if empty
    watchlist = db.get_watchlist()
    if not watchlist:
        for t in cfg.DEFAULT_WATCHLIST:
            db.add_to_watchlist(t)
        watchlist = cfg.DEFAULT_WATCHLIST

    effective_period, _api_key = _render_sidebar()

    st.header("📊 Investment Analysis")
    st.caption(
        f"Daily data · Period: **{effective_period}** · "
        f"Provider: **{st.session_state.inv_llm_provider}** · "
        f"{len(watchlist)} stocks"
    )

    # Auto-load on first visit or when period changes
    if not st.session_state.inv_data_loaded:
        _load_indicators(watchlist, effective_period)

    # Reload if new tickers have no indicators yet
    watchlist = db.get_watchlist()
    missing = [t for t in watchlist if t not in st.session_state.inv_indicators]
    if missing:
        _load_indicators(missing, effective_period)

    # Also load cached LLM results from DB
    for ticker in watchlist:
        if ticker not in st.session_state.inv_llm_results:
            cached = db.get_llm_cache(ticker, effective_period, st.session_state.inv_llm_provider)
            if cached:
                st.session_state.inv_llm_results[ticker] = cached

    st.subheader("Watchlist Overview")
    _render_overview_table(watchlist)

    st.subheader("Detailed Analysis")
    _render_detail_expanders(watchlist, effective_period)
