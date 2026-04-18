from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    full_name: str
    role: str
    org_id: int
    is_active: bool
    created_at: datetime


class OrgOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    industry: str | None = None
    country: str | None = None
    base_year: int | None = None
    net_zero_target_year: int | None = None
    carbon_price_inr_per_tonne: float
    fiscal_year_start_month: int
    onboarding_completed_at: datetime | None
    created_at: datetime


class MeResponse(BaseModel):
    user: UserOut
    organization_name: str
    organization: OrgOut


class SignupRequest(BaseModel):
    # Org fields
    company_name: str = Field(min_length=2, max_length=200)
    industry: str = Field(min_length=2, max_length=100)
    country: str = Field(min_length=2, max_length=100)
    fiscal_year_start_month: int = Field(ge=1, le=12, default=4)
    base_year: int = Field(ge=2000, le=2100, default_factory=lambda: datetime.utcnow().year)
    net_zero_target_year: int = Field(ge=2025, le=2100, default=2050)
    carbon_price_inr_per_tonne: float = Field(ge=0, default=2000.0)
    # First-admin fields
    admin_email: EmailStr
    admin_password: str = Field(min_length=8, max_length=72)
    admin_full_name: str = Field(min_length=1, max_length=200)


class SignupResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    organization: OrgOut
    user: UserOut


Role = Literal["admin", "analyst", "viewer"]


class InviteCreateRequest(BaseModel):
    email: EmailStr
    full_name: str | None = Field(default=None, max_length=200)
    role: Role


class InviteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    role: str
    expires_at: datetime
    accepted_at: datetime | None
    revoked_at: datetime | None
    invited_by_user_id: int
    created_at: datetime


class InviteCreateResponse(BaseModel):
    invite: InviteOut
    # One-time plaintext token — shown only on create. Frontend surfaces a link
    # like /accept-invite?token=... that a new user can click to complete signup.
    token: str
    invite_url_path: str


class InviteAcceptRequest(BaseModel):
    token: str
    password: str = Field(min_length=8, max_length=72)
    full_name: str = Field(min_length=1, max_length=200)


class TeamMemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime


class TeamListResponse(BaseModel):
    users: list[TeamMemberOut]
    pending_invites: list[InviteOut]


class OnboardingCompleteResponse(BaseModel):
    organization: OrgOut
