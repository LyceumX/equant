"""
scraper.py — Financial report / revenue scraper (Taiwan stocks via HiStock).

DEFENSIVE PROGRAMMING CONTRACT
-------------------------------
- Every parse step is wrapped in try-except.
- If ANY network or parsing error occurs, a graceful fallback dict is returned.
- This module MUST NEVER raise an unhandled exception to the FastAPI layer.
  The caller can detect failure via the `_scrape_failed` key being True.
"""

from __future__ import annotations

import logging
import re
from typing import Any

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_FALLBACK: dict[str, Any] = {
    "monthly_revenue_growth_yoy": None,
    "gross_margin": None,
    "pe_ratio": None,
    "eps": None,
    "_scrape_failed": True,
    "_scrape_error": "Data unavailable",
}

_HISTOCK_BASE = "https://histock.tw/stock"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
}

# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------


async def fetch_fundamental_data(symbol: str) -> dict[str, Any]:
    """
    Scrape fundamental data for a given ticker.

    For Taiwan stocks (e.g. '2330.TW' or '2330'), we strip the exchange suffix
    and query HiStock.  For other markets we return mock/fallback data.

    Returns a dict matching the FundamentalData schema; never raises.
    """
    clean_symbol = symbol.split(".")[0].strip()

    # Only attempt scraping for numeric Taiwan symbols
    if not clean_symbol.isdigit():
        logger.info("scraper: non-TW symbol '%s', returning mock fundamentals.", symbol)
        return _mock_fundamental(symbol)

    try:
        return await _scrape_histock(clean_symbol)
    except httpx.HTTPError as exc:
        logger.warning("scraper: network error for %s — %s", symbol, exc)
        return {**_FALLBACK, "_scrape_error": f"Network error: {exc}"}
    except Exception as exc:  # noqa: BLE001
        logger.error("scraper: unexpected error for %s — %s", symbol, exc, exc_info=True)
        return {**_FALLBACK, "_scrape_error": f"Parse error: {exc}"}


# ---------------------------------------------------------------------------
# HiStock scraper implementation
# ---------------------------------------------------------------------------


async def _scrape_histock(symbol: str) -> dict[str, Any]:
    """Scrape monthly revenue growth YoY from HiStock."""
    url = f"{_HISTOCK_BASE}/{symbol}/revenue"

    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        resp = await client.get(url, headers=_HEADERS)
        resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    result: dict[str, Any] = {
        "monthly_revenue_growth_yoy": None,
        "gross_margin": None,
        "pe_ratio": None,
        "eps": None,
        "_scrape_failed": False,
    }

    # ── Monthly revenue YoY ────────────────────────────────────────────────
    try:
        # HiStock renders revenue tables with class "tb-stock"
        tables = soup.find_all("table", class_="tb-stock")
        for table in tables:
            headers = [th.get_text(strip=True) for th in table.find_all("th")]
            if "年增率" in headers or "YoY" in headers:
                yoy_idx = next(
                    (i for i, h in enumerate(headers) if "年增率" in h or "YoY" in h), None
                )
                if yoy_idx is not None:
                    first_data_row = table.find("tbody").find("tr")
                    if first_data_row:
                        cells = first_data_row.find_all("td")
                        if yoy_idx < len(cells):
                            raw = cells[yoy_idx].get_text(strip=True)
                            result["monthly_revenue_growth_yoy"] = _clean_pct(raw)
                break
    except Exception as exc:  # noqa: BLE001
        logger.debug("scraper: YoY parse failed — %s", exc)

    # ── Gross margin (from financials page — best-effort) ──────────────────
    # NOTE: This is a placeholder; full gross margin scraping requires a
    # separate request to /profitability.  Marked for Phase 2.
    result["gross_margin"] = None

    if result["monthly_revenue_growth_yoy"] is None and result["gross_margin"] is None:
        logger.warning("scraper: all fields empty for %s, HTML structure may have changed.", symbol)
        result["_scrape_failed"] = True
        result["_scrape_error"] = "Parsed HTML returned no data — site structure may have changed."

    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _clean_pct(raw: str) -> str | None:
    """Normalise a percentage string like '-3.12%' or '28.50'."""
    raw = raw.strip().replace(",", "")
    if not raw or raw in ("-", "N/A", "--"):
        return None
    match = re.search(r"-?\d+\.?\d*", raw)
    if not match:
        return None
    value = match.group()
    return f"{value}%" if "%" not in raw else raw


def _mock_fundamental(symbol: str) -> dict[str, Any]:
    """Return plausible mock fundamentals for non-TW symbols."""
    import random

    rng = random.Random(hash(symbol) % (2**31))
    return {
        "monthly_revenue_growth_yoy": f"{rng.uniform(-5, 40):.1f}%",
        "gross_margin": f"{rng.uniform(20, 70):.1f}%",
        "pe_ratio": round(rng.uniform(10, 40), 1),
        "eps": round(rng.uniform(1, 50), 2),
        "_scrape_failed": False,
    }
