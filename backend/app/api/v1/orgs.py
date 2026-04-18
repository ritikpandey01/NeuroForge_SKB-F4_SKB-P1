"""Organization lifecycle endpoints.

POST /orgs/signup          — public; creates a new tenant + first admin atomically.
POST /orgs/complete-onboarding — admin; marks the current org's onboarding wizard done.

Signup is intentionally open so a prospective customer can self-serve onboard.
If you later want gated signups (invite-only SaaS), wrap this router in an
ADMIN_SIGNUP_KEY header check — the shape below stays the same.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.models import Organization, User, UserRole
from app.db.session import get_db
from app.schemas.auth import (
    OnboardingCompleteResponse,
    OrgOut,
    SignupRequest,
    SignupResponse,
    UserOut,
)
from app.services.auth import create_access_token, create_refresh_token, hash_password

router = APIRouter(prefix="/orgs")


@router.post(
    "/signup",
    response_model=SignupResponse,
    status_code=status.HTTP_201_CREATED,
)
def signup(body: SignupRequest, db: Session = Depends(get_db)) -> SignupResponse:
    email = body.admin_email.lower()

    # Pre-flight uniqueness: company name and admin email must be new. A race
    # here is still caught by the unique index on users.email, but the handler
    # returns a clean 409 instead of surfacing an IntegrityError.
    if db.scalar(select(Organization).where(Organization.name == body.company_name)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A company with this name already exists.",
        )
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    try:
        hashed = hash_password(body.admin_password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        ) from e

    org = Organization(
        name=body.company_name,
        industry=body.industry,
        country=body.country,
        base_year=body.base_year,
        net_zero_target_year=body.net_zero_target_year,
        carbon_price_inr_per_tonne=body.carbon_price_inr_per_tonne,
        fiscal_year_start_month=body.fiscal_year_start_month,
        onboarding_completed_at=None,  # gated until wizard finishes
    )
    db.add(org)
    db.flush()  # need org.id for the user

    user = User(
        email=email,
        password_hash=hashed,
        full_name=body.admin_full_name,
        role=UserRole.admin.value,
        org_id=org.id,
        is_active=True,
    )
    db.add(user)
    db.flush()

    db.commit()
    db.refresh(org)
    db.refresh(user)

    return SignupResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        organization=OrgOut.model_validate(org),
        user=UserOut.model_validate(user),
    )


@router.post(
    "/complete-onboarding",
    response_model=OnboardingCompleteResponse,
)
def complete_onboarding(
    user: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
) -> OnboardingCompleteResponse:
    org = db.get(Organization, user.org_id)
    if org is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )
    if org.onboarding_completed_at is None:
        org.onboarding_completed_at = datetime.utcnow()
        db.commit()
        db.refresh(org)
    return OnboardingCompleteResponse(organization=OrgOut.model_validate(org))
