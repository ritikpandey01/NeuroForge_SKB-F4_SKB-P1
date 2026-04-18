from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import Organization, User
from app.db.session import get_db
from app.schemas.auth import (
    LoginRequest,
    MeResponse,
    OrgOut,
    RefreshRequest,
    TokenResponse,
    UserOut,
)
from app.services.auth import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)

router = APIRouter(prefix="/auth")


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User is disabled"
        )
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        user_id = decode_token(body.refresh_token, expected_type="refresh")
    except TokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
        ) from e
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive"
        )
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.get("/me", response_model=MeResponse)
def me(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> MeResponse:
    org = db.get(Organization, user.org_id)
    if org is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )
    return MeResponse(
        user=UserOut.model_validate(user),
        organization_name=org.name,
        organization=OrgOut.model_validate(org),
    )
