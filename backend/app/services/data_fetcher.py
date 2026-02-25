"""
data_fetcher.py — External market data gateway.

Phase 1 (Mock): Returns deterministic fake OHLCV data so the full API chain
works before a real market data subscription is acquired.  Switch to a real
provider (Yahoo Finance via yfinance, Alpha Vantage, Futu OpenAPI, etc.) by
replacing the mock section below without touching the rest of the codebase.
"""

from __future__ import annotations

import logging
import random
from datetime import date, timedelta

import httpx

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

async def fetch_market_data(symbol: str, days: int = 30) -> dict:
    """
    Fetch OHLCV data and derive the latest price & volume.

    Returns:
        {
            "latest_price": float,
            "price_change_pct": float,
            "volume": int,
            "ohlcv": list[dict]   # list of {date, open, high, low, close, volume}
        }
    Falls back to mock data if the real fetch fails.
    """
    try:
        return await _fetch_from_yahoo(symbol, days)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "fetch_market_data(%s): real fetch failed (%s), using mock data.", symbol, exc
        )
        return _mock_market_data(symbol, days)


# ---------------------------------------------------------------------------
# Real implementation: Yahoo Finance (yfinance-compatible endpoint)
# ---------------------------------------------------------------------------

async def _fetch_from_yahoo(symbol: str, days: int) -> dict:
    """
    Calls the Yahoo Finance v8 chart API (no API key required).
    Raises httpx.HTTPError on any transport failure so the caller can fall back.
    """
    end_ts = int(date.today().strftime("%s") if hasattr(date.today(), "strftime") else 0)
    # Build URL for period2 = today, period1 = today - days
    import time

    period2 = int(time.time())
    period1 = period2 - days * 86_400
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        f"?period1={period1}&period2={period2}&interval=1d"
    )

    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        data = resp.json()

    result = data["chart"]["result"][0]
    timestamps = result["timestamp"]
    quotes = result["indicators"]["quote"][0]
    closes = quotes["close"]
    volumes = quotes["volume"]
    opens = quotes["open"]
    highs = quotes["high"]
    lows = quotes["low"]

    ohlcv = [
        {
            "date": date.fromtimestamp(ts).isoformat(),
            "open": opens[i],
            "high": highs[i],
            "low": lows[i],
            "close": closes[i],
            "volume": volumes[i],
        }
        for i, ts in enumerate(timestamps)
        if closes[i] is not None
    ]

    latest_price = ohlcv[-1]["close"]
    prev_price = ohlcv[-2]["close"] if len(ohlcv) > 1 else latest_price
    change_pct = round((latest_price - prev_price) / prev_price * 100, 2)

    return {
        "latest_price": round(latest_price, 2),
        "price_change_pct": change_pct,
        "volume": ohlcv[-1]["volume"] or 0,
        "ohlcv": ohlcv,
    }


# ---------------------------------------------------------------------------
# Mock fallback
# ---------------------------------------------------------------------------

def _mock_market_data(symbol: str, days: int) -> dict:
    """Deterministic seeded mock so UI development is consistent."""
    rng = random.Random(hash(symbol) % (2**31))
    base_price = rng.uniform(100, 1000)
    ohlcv = []
    today = date.today()

    price = base_price
    for i in range(days):
        d = today - timedelta(days=days - i)
        change = rng.uniform(-0.03, 0.03)
        close = round(price * (1 + change), 2)
        high = round(close * rng.uniform(1.001, 1.02), 2)
        low = round(close * rng.uniform(0.98, 0.999), 2)
        ohlcv.append(
            {
                "date": d.isoformat(),
                "open": round(price, 2),
                "high": high,
                "low": low,
                "close": close,
                "volume": rng.randint(10_000_000, 80_000_000),
            }
        )
        price = close

    latest = ohlcv[-1]["close"]
    prev = ohlcv[-2]["close"] if len(ohlcv) > 1 else latest
    return {
        "latest_price": latest,
        "price_change_pct": round((latest - prev) / prev * 100, 2),
        "volume": ohlcv[-1]["volume"],
        "ohlcv": ohlcv,
    }
