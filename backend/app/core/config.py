"""
Global application configuration loaded from environment variables.
Uses pydantic-settings for typed, validated config.

AI provider selection:
  Set AI_PROVIDER to "openai", "deepseek", or "google".
  The resolved ai_api_key / ai_api_base_url / ai_model properties
  automatically return the right values — no other code changes needed.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────────────────
    APP_NAME: str = "eQuant API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ── CORS ─────────────────────────────────────────────────────────────────
    CORS_ORIGINS: str = "https://equant.us.ci,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    # ── Supabase ─────────────────────────────────────────────────────────────
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""

    # ── Clerk ────────────────────────────────────────────────────────────────
    CLERK_ISSUER: str = ""
    CLERK_JWKS_URL: str = ""
    CLERK_SECRET_KEY: str = ""

    @property
    def clerk_jwks_url(self) -> str:
        if self.CLERK_JWKS_URL:
            return self.CLERK_JWKS_URL
        return f"{self.CLERK_ISSUER}/.well-known/jwks.json"

    # ── AI provider selection ────────────────────────────────────────────────
    AI_PROVIDER: Literal["openai", "deepseek", "google"] = "openai"

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # DeepSeek (OpenAI-compatible endpoint)
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_API_BASE_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # Google Generative AI
    GOOGLE_GENERATIVE_AI_API_KEY: str = ""
    GOOGLE_MODEL: str = "gemini-1.5-flash"

    # ── Resolved AI properties (used by ai_analyzer.py) ─────────────────────
    @property
    def ai_api_key(self) -> str:
        if self.AI_PROVIDER == "deepseek":
            return self.DEEPSEEK_API_KEY
        if self.AI_PROVIDER == "google":
            return self.GOOGLE_GENERATIVE_AI_API_KEY
        return self.OPENAI_API_KEY  # default: openai

    @property
    def ai_api_base_url(self) -> str:
        if self.AI_PROVIDER == "deepseek":
            return self.DEEPSEEK_API_BASE_URL
        if self.AI_PROVIDER == "google":
            # Google's OpenAI-compatible endpoint
            return "https://generativelanguage.googleapis.com/v1beta/openai"
        return "https://api.openai.com/v1"

    @property
    def ai_model(self) -> str:
        if self.AI_PROVIDER == "deepseek":
            return self.DEEPSEEK_MODEL
        if self.AI_PROVIDER == "google":
            return self.GOOGLE_MODEL
        return self.OPENAI_MODEL

    # ── External Market Data ─────────────────────────────────────────────────
    MARKET_DATA_API_KEY: str = ""


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings singleton."""
    return Settings()
