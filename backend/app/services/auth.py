"""Password hashing + JWT token helpers.

Kept as pure functions so handlers stay thin. Tokens carry only `sub` (user id)
and `type` (access | refresh); role + org_id are always re-read from the DB on
each request so a role change takes effect without forcing re-login.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

# bcrypt truncates silently at 72 bytes — reject anything longer so we never
# land in a state where two different long passwords map to the same hash.
_BCRYPT_MAX_BYTES = 72

TokenType = Literal["access", "refresh"]


def hash_password(plain: str) -> str:
    encoded = plain.encode("utf-8")
    if len(encoded) > _BCRYPT_MAX_BYTES:
        raise ValueError(
            f"password exceeds bcrypt's {_BCRYPT_MAX_BYTES}-byte limit"
        )
    return bcrypt.hashpw(encoded, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    encoded = plain.encode("utf-8")
    if len(encoded) > _BCRYPT_MAX_BYTES:
        return False
    try:
        return bcrypt.checkpw(encoded, hashed.encode("utf-8"))
    except ValueError:
        return False


def _create_token(user_id: int, token_type: TokenType, ttl: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + ttl).timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: int) -> str:
    return _create_token(
        user_id, "access", timedelta(minutes=settings.JWT_ACCESS_TTL_MINUTES)
    )


def create_refresh_token(user_id: int) -> str:
    return _create_token(
        user_id, "refresh", timedelta(days=settings.JWT_REFRESH_TTL_DAYS)
    )


class TokenError(Exception):
    pass


def decode_token(token: str, expected_type: TokenType) -> int:
    """Return the user_id encoded in the token. Raises TokenError on any problem."""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
    except JWTError as e:
        raise TokenError(f"invalid token: {e}") from e

    if payload.get("type") != expected_type:
        raise TokenError(f"expected {expected_type} token, got {payload.get('type')}")

    sub = payload.get("sub")
    if not sub:
        raise TokenError("token missing sub")
    try:
        return int(sub)
    except (TypeError, ValueError) as e:
        raise TokenError("token sub is not an integer") from e
