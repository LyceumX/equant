"""
main.py — FastAPI application entry point for eQuant backend.

Run locally:
    uvicorn app.main:app --reload --port 8000

Production (Gunicorn + Uvicorn workers):
    gunicorn app.main:app -k uvicorn.workers.UvicornWorker --workers 4 --bind 0.0.0.0:8000
"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api.v1 import analyze, backtest
from app.core.config import get_settings

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown hooks)
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logger.info("⚡  %s v%s starting up …", settings.APP_NAME, settings.APP_VERSION)
    if settings.ai_api_key:
        logger.info(
            "AI provider: %s | model: %s", settings.AI_PROVIDER, settings.ai_model
        )
    else:
        logger.warning(
            "No AI API key set for provider '%s' — summaries will use templates.",
            settings.AI_PROVIDER,
        )
    if not settings.SUPABASE_URL:
        logger.warning(
            "SUPABASE_URL is not set — Premium verification will fail."
        )
    yield
    logger.info("👋  %s shutting down.", settings.APP_NAME)


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "AI-assisted quantitative stock analysis platform backend. "
            "Provides market data aggregation, technical indicators, "
            "fundamental scraping, and AI-powered analysis."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── Middleware ─────────────────────────────────────────────────────────

    # CORS — allow Next.js dev server and any configured production domains
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Gzip compression for large JSON responses (equity curves etc.)
    app.add_middleware(GZipMiddleware, minimum_size=1024)

    # ── Request latency logging ────────────────────────────────────────────
    @app.middleware("http")
    async def log_requests(request: Request, call_next):  # noqa: ANN001
        start = time.perf_counter()
        response: Response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s → %d  (%.1f ms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response

    # ── Routers ──────────────────────────────────────────────────────────
    API_V1_PREFIX = "/api/v1"

    app.include_router(analyze.router, prefix=API_V1_PREFIX, tags=["Analysis"])
    app.include_router(backtest.router, prefix=API_V1_PREFIX, tags=["Backtest (Premium)"])

    # ── Health-check ─────────────────────────────────────────────────────
    @app.get("/health", tags=["Meta"], summary="Health check")
    async def health() -> dict:
        return {"status": "ok", "version": settings.APP_VERSION}

    return app


# ---------------------------------------------------------------------------
# App instance (Uvicorn entry-point: app.main:app)
# ---------------------------------------------------------------------------
app = create_app()
