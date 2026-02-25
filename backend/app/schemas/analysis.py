"""
Pydantic v2 models for the /api/v1/analyze endpoint.
All fields include Field(description=..., examples=[...]) for auto-generated
OpenAPI docs and for type safety across the whole codebase.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class TechnicalIndicators(BaseModel):
    rsi: float = Field(
        ...,
        description="Relative Strength Index (0–100). >70 overbought, <30 oversold.",
        examples=[65.2],
    )
    macd: str = Field(
        ...,
        description="Simplified MACD signal: 'bullish' | 'bearish' | 'neutral'.",
        examples=["bullish"],
    )
    ma20: float | None = Field(
        None,
        description="20-day simple moving average of closing price.",
        examples=[840.5],
    )
    ma60: float | None = Field(
        None,
        description="60-day simple moving average of closing price.",
        examples=[795.0],
    )


class MarketData(BaseModel):
    latest_price: float = Field(
        ...,
        description="Most recent closing price in the stock's local currency.",
        examples=[850.0],
    )
    price_change_pct: float | None = Field(
        None,
        description="Percentage price change versus previous close.",
        examples=[1.32],
    )
    volume: int | None = Field(
        None,
        description="Trading volume of the latest session.",
        examples=[28_500_000],
    )
    technical_indicators: TechnicalIndicators


class FundamentalData(BaseModel):
    monthly_revenue_growth_yoy: str | None = Field(
        None,
        description="Year-over-year monthly revenue growth rate, formatted as a percentage string.",
        examples=["28.5%"],
    )
    gross_margin: str | None = Field(
        None,
        description="Latest reported gross margin, formatted as a percentage string.",
        examples=["53%"],
    )
    pe_ratio: float | None = Field(
        None,
        description="Price-to-earnings ratio.",
        examples=[22.5],
    )
    eps: float | None = Field(
        None,
        description="Earnings per share (local currency).",
        examples=[37.8],
    )


# ---------------------------------------------------------------------------
# Response model
# ---------------------------------------------------------------------------

class AnalyzeResponse(BaseModel):
    symbol: str = Field(
        ...,
        description="Stock ticker symbol including exchange suffix.",
        examples=["2330.TW"],
    )
    market_data: MarketData
    fundamental_data: FundamentalData
    ai_summary: str = Field(
        ...,
        description="AI-generated plain-language analysis paragraph.",
        examples=["该股基本面强劲，营收大幅增长，技术面呈多头排列，短期看涨。"],
    )
    is_premium_analysis_available: bool = Field(
        ...,
        description="Whether deep AI premium analysis is available for this symbol.",
        examples=[True],
    )
