"""
ai_analyzer.py — Prompt assembly and LLM invocation.

Calls any OpenAI-compatible API (GPT-4o, DeepSeek, Qwen, etc.) by pointing
AI_API_BASE_URL at the provider's endpoint.
"""

from __future__ import annotations

import logging

from openai import AsyncOpenAI

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are a professional quantitative stock analyst. Given structured financial data,
write a concise, insightful, plain-language analysis (2-4 sentences) in the same
language the user uses. Be balanced: highlight both opportunities and risks.
Do NOT give explicit buy/sell advice.
"""


async def generate_ai_summary(
    symbol: str,
    market_data: dict,
    fundamental_data: dict,
) -> str:
    """
    Assemble a Prompt from structured data and call the configured LLM.

    The active provider is controlled by AI_PROVIDER in .env:
      - "openai"   → OpenAI API (default)
      - "deepseek" → DeepSeek API (OpenAI-compatible)
      - "google"   → Google Generative AI (OpenAI-compatible endpoint)

    Falls back to a templated string if the AI API call fails, so the
    endpoint never returns an error solely because of an AI outage.
    """
    settings = get_settings()

    if not settings.ai_api_key:
        logger.warning(
            "No API key configured for provider '%s' — returning template summary.",
            settings.AI_PROVIDER,
        )
        return _template_summary(symbol, market_data, fundamental_data)

    user_prompt = _build_user_prompt(symbol, market_data, fundamental_data)
    logger.debug(
        "generate_ai_summary(%s): using provider=%s model=%s",
        symbol, settings.AI_PROVIDER, settings.ai_model,
    )

    try:
        client = AsyncOpenAI(
            api_key=settings.ai_api_key,
            base_url=settings.ai_api_base_url,
        )
        response = await client.chat.completions.create(
            model=settings.ai_model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=300,
            temperature=0.4,
        )
        return response.choices[0].message.content.strip()

    except Exception as exc:  # noqa: BLE001
        logger.error(
            "AI API call failed for %s (provider=%s): %s",
            symbol, get_settings().AI_PROVIDER, exc,
        )
        return _template_summary(symbol, market_data, fundamental_data)


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------


def _build_user_prompt(symbol: str, market: dict, fundamentals: dict) -> str:
    indicators = market.get("technical_indicators", {})
    return f"""
Stock: {symbol}

Market Data:
- Latest Price: {market.get('latest_price', 'N/A')}
- Price Change: {market.get('price_change_pct', 'N/A')}%
- Volume: {market.get('volume', 'N/A')}

Technical Indicators:
- RSI (14): {indicators.get('rsi', 'N/A')}
- MACD Signal: {indicators.get('macd', 'N/A')}
- MA20: {indicators.get('ma20', 'N/A')}
- MA60: {indicators.get('ma60', 'N/A')}

Fundamental Data:
- Monthly Revenue Growth YoY: {fundamentals.get('monthly_revenue_growth_yoy', 'N/A')}
- Gross Margin: {fundamentals.get('gross_margin', 'N/A')}
- P/E Ratio: {fundamentals.get('pe_ratio', 'N/A')}
- EPS: {fundamentals.get('eps', 'N/A')}

Please provide a concise analysis.
""".strip()


# ---------------------------------------------------------------------------
# Fallback template (no AI key required)
# ---------------------------------------------------------------------------


def _template_summary(symbol: str, market: dict, fundamentals: dict) -> str:
    indicators = market.get("technical_indicators", {})
    rsi = indicators.get("rsi", 50)
    macd = indicators.get("macd", "neutral")
    yoy = fundamentals.get("monthly_revenue_growth_yoy")
    price = market.get("latest_price", "N/A")

    sentiment = "bullish" if macd == "bullish" and rsi < 70 else "bearish" if macd == "bearish" else "neutral"
    rev_note = f"with revenue YoY growth of {yoy}" if yoy else "with revenue data pending"

    return (
        f"{symbol} is currently priced at {price}, "
        f"{rev_note}. "
        f"Technical indicators show a {sentiment} setup (RSI {rsi:.1f}, MACD {macd}). "
        f"Investors should monitor volume and upcoming earnings for further confirmation."
    )
