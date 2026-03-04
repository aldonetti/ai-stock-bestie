"""Multi-provider LLM analysis for long-term investment recommendations."""

from typing import Dict, Optional

import config as cfg
import database as db


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def _build_prompt(ticker: str, indicators: Dict, period: str) -> str:
    """Build an investment-thesis prompt from indicator data."""

    def fmt(val: Optional[float], decimals: int = 2, suffix: str = "") -> str:
        if val is None:
            return "N/A"
        return f"{val:.{decimals}f}{suffix}"

    price = indicators.get("current_price", 0.0)
    trend_score = indicators.get("trend_score", 0.0)

    golden = indicators.get("golden_cross")
    cross_str = "Golden Cross (bullish)" if golden else "Death Cross (bearish)" if golden is False else "N/A"

    macd_hist = indicators.get("macd_histogram")
    macd_dir = "Positive (bullish momentum)" if (macd_hist is not None and macd_hist > 0) else "Negative (bearish momentum)"

    rsi = indicators.get("rsi")
    rsi_interp = ""
    if rsi is not None:
        if rsi > 70:
            rsi_interp = "(Overbought)"
        elif rsi < 30:
            rsi_interp = "(Oversold)"
        else:
            rsi_interp = "(Neutral)"

    bb_pos = indicators.get("bb_position")
    bb_interp = ""
    if bb_pos is not None:
        if bb_pos > 0.8:
            bb_interp = "(Near upper band — stretched)"
        elif bb_pos < 0.2:
            bb_interp = "(Near lower band — compressed)"
        else:
            bb_interp = "(Mid-range)"

    lines = [
        f"Stock: {ticker}  |  Analysis period: {period}",
        f"Current Price: ${price:.2f}",
        f"",
        f"== Moving Averages ==",
        f"SMA 50: {fmt(indicators.get('sma_50'), 2, '$' if False else '')}  (price {'above' if (v := indicators.get('sma_50')) and price > v else 'below'} SMA50)",
        f"SMA 200: {fmt(indicators.get('sma_200'))}  |  MA Crossover: {cross_str}",
        f"EMA 20: {fmt(indicators.get('ema_20'))}  |  EMA 50: {fmt(indicators.get('ema_50'))}",
        f"",
        f"== Momentum ==",
        f"RSI (14d): {fmt(rsi)} {rsi_interp}",
        f"MACD: {fmt(indicators.get('macd'))}  |  Signal: {fmt(indicators.get('macd_signal'))}  |  Histogram: {fmt(indicators.get('macd_histogram'))} — {macd_dir}",
        f"",
        f"== Volatility & Bands ==",
        f"Bollinger Bands: Upper {fmt(indicators.get('bb_upper'))} / Lower {fmt(indicators.get('bb_lower'))}  |  Position: {fmt(bb_pos, 1, '%' if bb_pos else '')} {bb_interp}",
        f"ATR (14d): {fmt(indicators.get('atr'))} ({fmt(indicators.get('atr_pct'))}% of price) — daily volatility estimate",
        f"",
        f"== 52-Week Levels ==",
        f"52w High: ${fmt(indicators.get('week52_high'))}  ({fmt(indicators.get('dist_from_52h_pct'))}% from high)",
        f"52w Low:  ${fmt(indicators.get('week52_low'))}  ({fmt(indicators.get('dist_from_52l_pct'))}% from low)",
        f"",
        f"== Performance ==",
        f"1M: {fmt(indicators.get('return_1m'))}%  |  3M: {fmt(indicators.get('return_3m'))}%  |  6M: {fmt(indicators.get('return_6m'))}%",
        f"1Y: {fmt(indicators.get('return_1y'))}%  |  YTD: {fmt(indicators.get('return_ytd'))}%",
        f"",
        f"== Volume ==",
        f"Volume trend (20d/50d avg ratio): {fmt(indicators.get('volume_trend'))}x  ({'increasing' if (vt := indicators.get('volume_trend')) and vt > 1 else 'decreasing'} volume)",
        f"",
        f"== Composite Signal ==",
        f"Trend Score: {trend_score:.2f} (scale: -1=strong bear, 0=neutral, +1=strong bull)",
    ]

    body = "\n".join(lines)

    return f"""You are a professional equity analyst specializing in medium-to-long-term investment analysis (investment horizon: weeks to months, not day-trading).

Analyze the following technical data for {ticker} over the past {period}:

{body}

Provide a structured investment analysis (max 250 words) covering:
1. **Trend Analysis** — Is the stock in an uptrend, downtrend, or consolidation? What do the MA signals say?
2. **Momentum & Strength** — RSI and MACD interpretation for the investment horizon
3. **Risk Assessment** — Volatility (ATR), distance from 52w extremes, Bollinger position
4. **Performance Context** — How has the stock performed recently vs longer timeframes?
5. **Investment Recommendation** — BUY / HOLD / SELL with a brief rationale

Format your response as:
**Trend Analysis**
[Your analysis]

**Momentum & Strength**
[Your analysis]

**Risk Assessment**
[Your analysis]

**Performance Context**
[Your analysis]

**Investment Recommendation: [BUY / HOLD / SELL]**
[Your rationale — 2-3 sentences with key supporting reasons]

Be direct and actionable. Focus on investment suitability, not intraday trading."""


# ---------------------------------------------------------------------------
# Provider implementations
# ---------------------------------------------------------------------------

def _call_ollama(prompt: str) -> Optional[str]:
    try:
        import ollama
        response = ollama.chat(
            model=cfg.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": 0.5,
                "num_predict": 500,
                "top_p": 0.9,
            },
            stream=False,
        )
        if isinstance(response, dict):
            msg = response.get("message", {})
            if isinstance(msg, dict):
                return msg.get("content", "")
        if hasattr(response, "message") and hasattr(response.message, "content"):
            return response.message.content
        return str(response)
    except Exception as e:
        return f"Ollama error: {e}"


def _call_openai(prompt: str, api_key: str, model: Optional[str] = None) -> Optional[str]:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=model or cfg.OPENAI_DEFAULT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.5,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"OpenAI error: {e}"


def _call_anthropic(prompt: str, api_key: str, model: Optional[str] = None) -> Optional[str]:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model=model or cfg.ANTHROPIC_DEFAULT_MODEL,
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text if msg.content else None
    except Exception as e:
        return f"Anthropic error: {e}"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_investment_analysis(
    ticker: str,
    indicators: Dict,
    period: str,
    provider: str = cfg.LLM_PROVIDER_OLLAMA,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    use_cache: bool = True,
) -> Optional[str]:
    """
    Generate an investment analysis using the specified LLM provider.

    Args:
        ticker: Stock ticker symbol
        indicators: Dict from long_term_indicators.calculate_investment_indicators
        period: Period label used for the analysis
        provider: One of cfg.LLM_PROVIDERS
        api_key: Required for OpenAI/Anthropic
        model: Optional model override
        use_cache: If True, check DB cache before calling LLM (24h TTL)

    Returns:
        Analysis text or None on failure
    """
    ticker = ticker.upper()

    if use_cache:
        cached = db.get_llm_cache(ticker, period, provider)
        if cached:
            return cached

    prompt = _build_prompt(ticker, indicators, period)

    if provider == cfg.LLM_PROVIDER_OLLAMA:
        result = _call_ollama(prompt)
    elif provider == cfg.LLM_PROVIDER_OPENAI:
        if not api_key:
            return "OpenAI API key is required."
        result = _call_openai(prompt, api_key, model)
    elif provider == cfg.LLM_PROVIDER_ANTHROPIC:
        if not api_key:
            return "Anthropic API key is required."
        result = _call_anthropic(prompt, api_key, model)
    else:
        return f"Unknown provider: {provider}"

    if result and not result.startswith(("Ollama error", "OpenAI error", "Anthropic error")):
        db.set_llm_cache(ticker, period, provider, result)

    return result
