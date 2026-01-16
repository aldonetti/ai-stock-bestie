"""LLM-powered insights generation with caching."""

import re
import time
from typing import Dict, Optional

import ollama
import streamlit as st

import config as cfg

_TRADING_TERMS_PATTERN = re.compile(
    r"([a-z])(Bollinger|Bands|RSI|MACD|VWAP|Support|Resistance|Momentum|Volume|Price|Trend|Level|Above|Below|Overbought|Oversold)",
    re.IGNORECASE,
)

_COMMON_PHRASES_PATTERNS = [
    (
        re.compile(
            r"\b(The|is|are|with|above|below|price|position|trading|recommend|holding|onto|information|given)([a-z])",
            re.IGNORECASE,
        ),
        r"\1 \2",
    ),
    (re.compile(r"\b(both)([A-Z])"), r"\1 \2"),
]

_FIX_PATTERNS = [
    (re.compile(r"\s+([,.!?;:])"), r"\1"),
    (re.compile(r"([,.!?;:])([A-Za-z])"), r"\1 \2"),
    (re.compile(r"([a-z])(,)([a-z])", re.IGNORECASE), r"\1\2 \3"),
    (re.compile(r"([a-z])(\$\d)", re.IGNORECASE), r"\1 \2"),
    (re.compile(r"(\d)([A-Za-z])"), r"\1 \2"),
    (re.compile(r" +"), " "),
]


def fix_text_spacing(text: str) -> str:
    """Fix text spacing issues in LLM output."""
    if not text:
        return text

    text = re.sub(r"([a-z])([A-Z][a-z])", r"\1 \2", text)
    text = _TRADING_TERMS_PATTERN.sub(r"\1 \2", text)

    for pattern, replacement in _COMMON_PHRASES_PATTERNS:
        text = pattern.sub(replacement, text)

    for pattern, replacement in _FIX_PATTERNS:
        text = pattern.sub(replacement, text)

    return text.strip()


def generate_insights_prompt(insights: Dict, ticker: str) -> str:
    """
    Generate optimized prompt for LLM analysis.

    Args:
        insights: Dictionary of technical indicators
        ticker: Stock ticker symbol

    Returns:
        Formatted prompt string
    """
    current_price = insights.get("current_price", 0.0)
    rolling_avg = insights.get("rolling_avg", 0.0)
    ema_short = insights.get("ema_short", 0.0)
    price_change = insights.get("price_change", 0.0)
    price_change_pct = insights.get("price_change_pct", 0.0)
    volume_change = insights.get("volume_change", 0.0)

    parts = [
        f"Current Price: ${current_price:.2f}",
        f"Rolling Average: ${rolling_avg:.2f}",
        f"EMA Short ({cfg.EMA_SHORT}): ${ema_short:.2f}",
    ]

    ema_long = insights.get("ema_long")
    if ema_long is not None and isinstance(ema_long, (int, float)):
        parts.append(f"EMA Long ({cfg.EMA_LONG}): ${ema_long:.2f}")

    parts.extend(
        [
            f"Price Change: ${price_change:.2f} ({price_change_pct:.2f}%)",
            f"Volume Change: {volume_change:,.0f} shares",
        ]
    )

    volume_ratio = insights.get("volume_ratio")
    if volume_ratio is not None and isinstance(volume_ratio, (int, float)):
        parts.append(f"Volume Ratio: {volume_ratio:.2f}x average")

    bollinger_upper = insights.get("bollinger_upper")
    bollinger_lower = insights.get("bollinger_lower")
    bb_position = insights.get("bb_position")
    if (
        bollinger_upper is not None
        and bollinger_lower is not None
        and bb_position is not None
        and isinstance(bollinger_upper, (int, float))
        and isinstance(bollinger_lower, (int, float))
        and isinstance(bb_position, (int, float))
    ):
        parts.extend(
            [
                f"Bollinger Bands: Upper ${bollinger_upper:.2f}, Lower ${bollinger_lower:.2f}",
                f"Price Position in Bands: {bb_position*100:.1f}%",
            ]
        )

    rsi_val = insights.get("rsi")
    if rsi_val is not None and isinstance(rsi_val, (int, float)):
        rsi_status = (
            "(Overbought)" if rsi_val > 70 else "(Oversold)" if rsi_val < 30 else "(Neutral)"
        )
        parts.append(f"RSI: {rsi_val:.2f} {rsi_status}")

    macd_val = insights.get("macd")
    signal_val = insights.get("signal")
    histogram_val = insights.get("histogram")
    if (
        macd_val is not None
        and signal_val is not None
        and histogram_val is not None
        and isinstance(macd_val, (int, float))
        and isinstance(signal_val, (int, float))
        and isinstance(histogram_val, (int, float))
    ):
        parts.append(
            f"MACD: {macd_val:.2f}, "
            f"Signal: {signal_val:.2f}, "
            f"Histogram: {histogram_val:.2f}"
        )

    support_val = insights.get("support")
    if support_val is not None and isinstance(support_val, (int, float)):
        parts.append(f"Support Level: ${support_val:.2f}")

    resistance_val = insights.get("resistance")
    if resistance_val is not None and isinstance(resistance_val, (int, float)):
        parts.append(f"Resistance Level: ${resistance_val:.2f}")

    vwap_val = insights.get("vwap")
    if vwap_val is not None and isinstance(vwap_val, (int, float)):
        parts.append(f"VWAP: ${vwap_val:.2f}")

    daily_high = insights.get("daily_high")
    if daily_high is None:
        daily_high = st.session_state.get("daily_high", 0.0)
        if daily_high == float("-inf"):
            daily_high = current_price

    daily_low = insights.get("daily_low")
    if daily_low is None:
        daily_low = st.session_state.get("daily_low", 0.0)
        if daily_low == float("inf"):
            daily_low = current_price

    buying_momentum = insights.get("buying_momentum")
    if buying_momentum is None:
        buying_momentum = st.session_state.get("buying_momentum", 0.0)

    selling_momentum = insights.get("selling_momentum")
    if selling_momentum is None:
        selling_momentum = st.session_state.get("selling_momentum", 0.0)

    market_price_change = insights.get("market_price_change", 0.0)

    if (
        isinstance(daily_high, (int, float))
        and isinstance(daily_low, (int, float))
        and daily_low > 0
    ):
        daily_range_pct = ((daily_high - daily_low) / daily_low) * 100
    else:
        daily_range_pct = 0.0

    parts.extend(
        [
            f"Daily High: ${daily_high:.2f}",
            f"Daily Low: ${daily_low:.2f}",
            f"Daily Range: {daily_range_pct:.2f}%",
            f"Buying Momentum (last 20 periods): ${buying_momentum:.2f}",
            f"Selling Momentum (last 20 periods): ${selling_momentum:.2f}",
            f"Market (SPY) Change: ${market_price_change:.2f}",
        ]
    )

    return f"""You are a professional stock analyst. Analyze the following technical indicators for {ticker} stock:

{chr(10).join(parts)}

Provide a complete, actionable analysis (max 200 words) focusing on:
1. Current trend direction
2. Key support/resistance levels
3. Momentum indicators
4. Volume analysis
5. Complete trading recommendation with clear action

Requirements:
- Write clear, well-formatted sentences with proper spacing
- Use proper punctuation and formatting
- Complete all recommendations without truncation
- End with a complete conclusion paragraph summarizing the recommendation
- Conclusion must include: recommended action (BUY/HOLD/SELL), entry/exit strategy, and risk management

Format your response as:
**Analysis**
[Your analysis here]

**Trading Recommendation**
[Your complete recommendation with entry/exit points]

**Conclusion**
[Your complete conclusion - must be a full paragraph ending with a clear final statement]

Start directly with the analysis and ensure you complete your full recommendation including the conclusion."""


def get_llm_insights(insights: Dict, ticker: str, use_cache: bool = True) -> Optional[str]:
    """
    Generate AI-powered insights with caching.

    Args:
        insights: Dictionary of technical indicators
        ticker: Stock ticker symbol
        use_cache: Whether to use cached responses

    Returns:
        AI-generated insight text or None if error
    """
    if not insights:
        return None

    if use_cache and st.session_state.get("last_llm_response"):
        cache_age = (
            time.time() - st.session_state.llm_cache_time
            if st.session_state.get("llm_cache_time")
            else float("inf")
        )
        if cache_age < cfg.LLM_CACHE_DURATION:
            return st.session_state.last_llm_response  # type: ignore[no-any-return]

    try:
        if insights is None or not isinstance(insights, dict):
            return "Error: Invalid insights data - cannot generate analysis"

        required_keys = [
            "current_price",
            "rolling_avg",
            "ema_short",
            "price_change",
            "price_change_pct",
            "volume_change",
            "bollinger_upper",
            "bollinger_lower",
            "bb_position",
            "market_price_change",
        ]
        missing_keys = [
            key for key in required_keys if key not in insights or insights.get(key) is None
        ]
        if missing_keys:
            pass

        if not all(
            isinstance(insights.get(key), (int, float))
            for key in ["current_price", "rolling_avg", "ema_short"]
        ):
            return "Error: Invalid indicator values - cannot generate analysis"

        try:
            prompt = generate_insights_prompt(insights, ticker)
        except Exception as e:
            return f"Error generating prompt: {str(e)}"

        try:
            response = ollama.chat(
                model=cfg.LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                options={
                    "temperature": max(0.3, min(0.7, cfg.LLM_TEMPERATURE)),
                    "num_predict": cfg.LLM_MAX_TOKENS,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1,
                    "stop": [],
                },
                stream=False,
            )

            result = None

            if isinstance(response, dict):
                if "message" in response:
                    message = response["message"]
                    if isinstance(message, dict):
                        if "content" in message:
                            result = message["content"]
                    else:
                        try:
                            result = getattr(message, "content", None)
                        except (AttributeError, TypeError):
                            pass

                        if result is None:
                            try:
                                if isinstance(message, dict):
                                    result = message.get("content", None)
                                elif hasattr(message, "__getitem__"):
                                    result = message["content"]
                            except (KeyError, TypeError, AttributeError):
                                pass

                        if result is None and isinstance(message, str):
                            result = message

                if result is None and "content" in response:
                    result = response["content"]

            elif isinstance(response, str):
                result = response

            elif hasattr(response, "content"):
                try:
                    result = getattr(response, "content", None)
                except Exception:
                    pass

            if result is None or not result:
                import re

                response_str = str(response)

                content_match = re.search(
                    r"content='(.*?)(?:',\s*(?:thinking|tool_name|images)=|'$|$)",
                    response_str,
                    re.DOTALL,
                )
                if not content_match:
                    content_match = re.search(r"content='(.*?)'", response_str, re.DOTALL)
                if not content_match:
                    content_match = re.search(r'content="(.*?)"', response_str, re.DOTALL)

                if content_match:
                    result = content_match.group(1)
                    result = (
                        result.replace("\\n", "\n")
                        .replace("\\t", "\t")
                        .replace('\\"', '"')
                        .replace("\\'", "'")
                    )
                else:
                    content_match = re.search(
                        r"content=(.*?)(?:,\s*\w+=|\))", response_str, re.DOTALL
                    )
                    if content_match:
                        result = content_match.group(1).strip("'\"")
                    else:
                        result = "No response content found from AI model"

            if not isinstance(result, str):
                result = str(result)

            result = result.strip()
            result = (
                result.replace("\\n", "\n")
                .replace("\\t", "\t")
                .replace('\\"', '"')
                .replace("\\'", "'")
            )

            if result:
                has_conclusion_section = "**Conclusion**" in result
                ends_properly = result.strip().endswith((".", "!", "?"))

                if has_conclusion_section:
                    conclusion_part = result.split("**Conclusion**")[-1].strip()
                    if conclusion_part and not conclusion_part[-1] in ".!?":
                        result += "\n\nAnalysis may be incomplete. Review indicators carefully."
                elif not ends_properly:
                    last_words = result.split()[-3:] if len(result.split()) >= 3 else result.split()
                    if last_words and len(last_words[-1]) < 4:
                        result += "\n\nAnalysis may be incomplete. Review all indicators before making trading decisions."

            if not result:
                result = "No response content received from AI model"

        except Exception as e:
            return f"Error calling AI model: {str(e)}"

        result = fix_text_spacing(result)

        if use_cache:
            st.session_state.last_llm_response = result
            st.session_state.llm_cache_time = time.time()

        return result
    except ValueError as e:
        if "not enough values to unpack" in str(e) or "expected" in str(e) and "got" in str(e):
            return f"Error: Data format issue - {str(e)}. Please try again."
        return f"Error generating insights: {str(e)}"
    except Exception as e:
        return f"Error generating insights: {str(e)}"
