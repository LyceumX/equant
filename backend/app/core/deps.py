"""
FastAPI dependency injection helpers.
- get_current_user  : validates Clerk JWT and returns the decoded payload
- get_premium_user  : additionally verifies the user has a Premium role in Supabase

DEBUG / LOCAL DEVELOPMENT
--------------------------
When DEBUG=true in .env the bearer token is OPTIONAL.
If no (or an invalid) token is supplied, a mock user payload is injected:
    { "sub": "dev_user_local", "email": "dev@local.test", "debug": true }
This lets you hit every endpoint with a plain curl/httpie call while the
production Clerk domain (equant.us.ci) is still pending.

NEVER set DEBUG=true in production.
"""

from __future__ import annotations

import logging
from typing import Annotated, Any

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwk, jwt
from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

# auto_error=False so we can handle missing tokens gracefully in DEBUG mode
bearer_scheme = HTTPBearer(auto_error=False)

_DEBUG_USER: dict[str, Any] = {
    "sub": "dev_user_local",
    "email": "dev@local.test",
    "debug": True,
}


# ---------------------------------------------------------------------------
# JWKS cache (simple in-process; use Redis for multi-worker production)
# ---------------------------------------------------------------------------
_jwks_cache: dict[str, Any] | None = None


async def _fetch_jwks(settings: Settings) -> dict[str, Any]:
    global _jwks_cache
    if _jwks_cache:
        return _jwks_cache

    async with httpx.AsyncClient(timeout=5) as client:
        resp = await client.get(settings.clerk_jwks_url)
        resp.raise_for_status()
        _jwks_cache = resp.json()
        return _jwks_cache


# ---------------------------------------------------------------------------
# JWT verification
# ---------------------------------------------------------------------------

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, Any]:
    """
    Verify the Clerk-issued JWT.
    Returns the decoded token payload on success.
    Raises HTTP 401 on any failure.

    In DEBUG mode: if no token (or an invalid one) is provided, returns a
    mock dev user instead of raising 401.
    """
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # ── DEBUG bypass ──────────────────────────────────────────────────────
    if settings.DEBUG:
        if not credentials:
            logger.debug("DEBUG mode: no token supplied — injecting mock user.")
            return _DEBUG_USER
        # If a token IS present in debug mode, still try to validate it;
        # fall back to mock user on any failure so curl -H 'Authorization: Bearer dummy' works.
        try:
            return await _verify_jwt(credentials.credentials, settings)
        except HTTPException:
            logger.debug("DEBUG mode: token invalid — injecting mock user.")
            return _DEBUG_USER

    # ── Production: token required ────────────────────────────────────────
    if not credentials:
        raise credential_exception

    return await _verify_jwt(credentials.credentials, settings)


async def _verify_jwt(token: str, settings: Settings) -> dict[str, Any]:
    """Validate a Clerk JWT against the JWKS endpoint."""
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        jwks = await _fetch_jwks(settings)
        matching_keys = [k for k in jwks.get("keys", []) if k.get("kid") == kid]
        if not matching_keys:
            raise credential_exception

        public_key = jwk.construct(matching_keys[0])
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            issuer=settings.CLERK_ISSUER or None,
            options={"verify_aud": False},
        )
        return payload
    except JWTError as exc:
        logger.warning("JWT validation failed: %s", exc)
        raise credential_exception from exc


# ---------------------------------------------------------------------------
# Premium guard (checks Supabase `profiles` table)
# ---------------------------------------------------------------------------

async def get_premium_user(
    user: Annotated[dict[str, Any], Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, Any]:
    """
    Verify that the authenticated user has a 'premium' role stored in Supabase.
    Raises HTTP 403 with upgrade message if not Premium.

    In DEBUG mode: the mock dev user is treated as Premium so the backtest
    endpoint is fully testable without a real Supabase profiles row.
    """
    # DEBUG: treat mock user as premium
    if settings.DEBUG and user.get("debug"):
        logger.debug("DEBUG mode: granting Premium to mock dev user.")
        return user

    user_id: str = user.get("sub", "")

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/profiles",
                params={"user_id": f"eq.{user_id}", "select": "role"},
                headers={
                    "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                    "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                },
            )
            resp.raise_for_status()
            rows = resp.json()
    except httpx.HTTPError as exc:
        logger.error("Supabase profile lookup failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not verify subscription status.",
        ) from exc

    if not rows or rows[0].get("role") != "premium":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Upgrade to Premium to unlock.",
        )

    return user
