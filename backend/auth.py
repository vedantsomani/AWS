"""JWT authentication middleware for Supabase tokens."""

from __future__ import annotations

import logging
import os
from typing import Any

import jwt
from fastapi import HTTPException, Query, WebSocket, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)

_security = HTTPBearer(auto_error=False)


def _get_jwt_secret() -> str:
    secret = os.getenv("SUPABASE_JWT_SECRET")
    if not secret:
        raise RuntimeError("SUPABASE_JWT_SECRET environment variable is not set.")
    return secret


def verify_token(token: str) -> dict[str, Any]:
    """Verify a Supabase JWT and return the decoded payload."""
    secret = _get_jwt_secret()
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired.")
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid token: {exc}")


def get_user_id_from_token(token: str) -> str:
    """Extract the user ID (sub) from a verified JWT."""
    payload = verify_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token missing 'sub' claim.")
    return user_id


async def get_ws_user_id(ws: WebSocket, token: str | None = Query(default=None)) -> str | None:
    """Extract user ID from WebSocket query param token. Returns None if auth is disabled or skipped."""
    jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
    if not jwt_secret:
        # Auth not configured — allow unauthenticated access in dev
        return None

    if not token:
        # No token provided — allow anonymous access (mock login mode)
        logger.debug("No token provided for WebSocket — allowing anonymous access.")
        return None

    try:
        return get_user_id_from_token(token)
    except HTTPException:
        # Invalid token — allow anonymous access instead of closing
        logger.warning("Invalid token provided for WebSocket — allowing anonymous access.")
        return None
