"""
analyze.py — GET /api/v1/analyze/{symbol}

Business logic:
  1. Parallel-fetch market data (data_fetcher) + fundamental data (scraper)
  2. Compute technical indicators (qlib_wrapper)
  3. Assemble prompt → call LLM (ai_analyzer)
  4. Return typed AnalyzeResponse
"""

from __future__ import annotations

import asyncio
import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_user
from app.schemas.analysis import (
    AnalyzeResponse,
    FundamentalData,
    MarketData,
    TechnicalIndicators,
)
from app.services import ai_analyzer, data_fetcher, qlib_wrapper, scraper

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/analyze/{symbol}",
    response_model=AnalyzeResponse,
    summary="Comprehensive stock analysis",
    description=(
        "Fetches market data + fundamentals in parallel, computes technical "
        "indicators, and returns an AI-generated summary. Requires a valid Clerk JWT."
    ),
)
async def analyze_stock(
    symbol: str,
    _user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> AnalyzeResponse:
    # ── 1. Parallel I/O: market data + fundamentals ──────────────────────
    market_task = asyncio.create_task(data_fetcher.fetch_market_data(symbol, days=30))
    fundamental_task = asyncio.create_task(scraper.fetch_fundamental_data(symbol))

    try:
        market_raw, fundamental_raw = await asyncio.gather(market_task, fundamental_task)
    except Exception as exc:
        logger.error("analyze_stock(%s): data fetch error — %s", symbol, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Upstream data fetch failed: {exc}",
        ) from exc

    # ── 2. Technical indicators ───────────────────────────────────────────
    indicators_raw = qlib_wrapper.compute_indicators(market_raw.get("ohlcv", []))

    # ── 3. Assemble nested market_data dict for AI prompt ────────────────
    market_with_indicators = {**market_raw, "technical_indicators": indicators_raw}

    # ── 4. AI summary ─────────────────────────────────────────────────────
    ai_summary = await ai_analyzer.generate_ai_summary(
        symbol=symbol,
        market_data=market_with_indicators,
        fundamental_data=fundamental_raw,
    )

    # ── 5. Build typed response ───────────────────────────────────────────
    return AnalyzeResponse(
        symbol=symbol,
        market_data=MarketData(
            latest_price=market_raw["latest_price"],
            price_change_pct=market_raw.get("price_change_pct"),
            volume=market_raw.get("volume"),
            technical_indicators=TechnicalIndicators(
                rsi=indicators_raw["rsi"],
                macd=indicators_raw["macd"],
                ma20=indicators_raw.get("ma20"),
                ma60=indicators_raw.get("ma60"),
            ),
        ),
        fundamental_data=FundamentalData(
            monthly_revenue_growth_yoy=fundamental_raw.get("monthly_revenue_growth_yoy"),
            gross_margin=fundamental_raw.get("gross_margin"),
            pe_ratio=fundamental_raw.get("pe_ratio"),
            eps=fundamental_raw.get("eps"),
        ),
        ai_summary=ai_summary,
        is_premium_analysis_available=True,
    )
