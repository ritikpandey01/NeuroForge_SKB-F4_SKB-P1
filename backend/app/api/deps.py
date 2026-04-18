"""Shared FastAPI dependencies for auth and org-scoping.

`get_current_user` decodes the Bearer token, loads the User row (confirming
still active), and returns it. `require_role(*roles)` wraps it with a role
check. Endpoint handlers use these to get both the acting user and their
`org_id` for scoped queries.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.models import User, UserRole
from app.db.session import get_db
from app.services.auth import TokenError, decode_token

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user_id = decode_token(creds.credentials, expected_type="access")
    except TokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive"
        )
    return user


def require_role(*allowed: UserRole):
    allowed_values = {r.value for r in allowed}

    def _check(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role in {sorted(allowed_values)}",
            )
        return user

    return _check
