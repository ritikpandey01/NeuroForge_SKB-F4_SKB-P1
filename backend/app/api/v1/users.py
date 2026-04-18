"""Team management — user invites + list + deactivate.

Invite flow:
  admin  → POST /users/invite     → returns one-time token (logged server-side)
  invitee → POST /users/accept-invite {token, password, full_name}

We do NOT send email from the server — the token is returned to the inviting
admin so they can paste the link into whatever channel they use (Slack, email,
etc.). Swap this for a real mailer when productionizing.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.db.models import User, UserInvite, UserRole
from app.db.session import get_db
from app.schemas.auth import (
    InviteAcceptRequest,
    InviteCreateRequest,
    InviteCreateResponse,
    InviteOut,
    TeamListResponse,
    TeamMemberOut,
    TokenResponse,
)
from app.services.auth import (
    create_access_token,
    create_refresh_token,
    hash_password,
)

router = APIRouter(prefix="/users")

_INVITE_TTL = timedelta(days=7)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _valid_role(raw: str) -> UserRole:
    try:
        return UserRole(raw)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid role '{raw}'. Expected admin/analyst/viewer.",
        ) from e


@router.get("", response_model=TeamListResponse)
def list_team(
    user: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
) -> TeamListResponse:
    users = list(
        db.scalars(
            select(User).where(User.org_id == user.org_id).order_by(User.created_at)
        ).all()
    )
    invites = list(
        db.scalars(
            select(UserInvite)
            .where(
                UserInvite.org_id == user.org_id,
                UserInvite.accepted_at.is_(None),
                UserInvite.revoked_at.is_(None),
            )
            .order_by(UserInvite.created_at.desc())
        ).all()
    )
    return TeamListResponse(
        users=[TeamMemberOut.model_validate(u) for u in users],
        pending_invites=[InviteOut.model_validate(i) for i in invites],
    )


@router.post(
    "/invite",
    response_model=InviteCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_invite(
    body: InviteCreateRequest,
    user: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
) -> InviteCreateResponse:
    role = _valid_role(body.role)
    email = body.email.lower()

    # Same email can't already be a user in ANY org — users.email is globally unique.
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    # Revoke any older pending invites for the same email in this org so only the
    # newest token is valid. Keeps the flow clean if an admin re-invites.
    existing_pending = db.scalars(
        select(UserInvite).where(
            UserInvite.org_id == user.org_id,
            UserInvite.email == email,
            UserInvite.accepted_at.is_(None),
            UserInvite.revoked_at.is_(None),
        )
    ).all()
    now = datetime.utcnow()
    for inv in existing_pending:
        inv.revoked_at = now

    raw_token = secrets.token_urlsafe(32)
    invite = UserInvite(
        org_id=user.org_id,
        email=email,
        role=role.value,
        token_hash=_hash_token(raw_token),
        invited_by_user_id=user.id,
        expires_at=now + _INVITE_TTL,
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)

    return InviteCreateResponse(
        invite=InviteOut.model_validate(invite),
        token=raw_token,
        invite_url_path=f"/accept-invite?token={raw_token}",
    )


@router.post("/accept-invite", response_model=TokenResponse)
def accept_invite(body: InviteAcceptRequest, db: Session = Depends(get_db)) -> TokenResponse:
    token_hash = _hash_token(body.token)
    invite = db.scalar(select(UserInvite).where(UserInvite.token_hash == token_hash))
    if invite is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found."
        )
    now = datetime.utcnow()
    if invite.accepted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Invite already accepted."
        )
    if invite.revoked_at is not None:
        raise HTTPException(
            status_code=status.HTTP_410_GONE, detail="Invite revoked."
        )
    if invite.expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_410_GONE, detail="Invite expired."
        )
    if db.scalar(select(User).where(User.email == invite.email)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    try:
        hashed = hash_password(body.password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        ) from e

    user = User(
        email=invite.email,
        password_hash=hashed,
        full_name=body.full_name,
        role=invite.role,
        org_id=invite.org_id,
        is_active=True,
    )
    db.add(user)
    invite.accepted_at = now
    db.commit()
    db.refresh(user)

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.delete(
    "/invites/{invite_id}", status_code=status.HTTP_204_NO_CONTENT
)
def revoke_invite(
    invite_id: int,
    user: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
) -> None:
    invite = db.get(UserInvite, invite_id)
    if invite is None or invite.org_id != user.org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found."
        )
    if invite.accepted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot revoke an already-accepted invite.",
        )
    if invite.revoked_at is None:
        invite.revoked_at = datetime.utcnow()
        db.commit()


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_user(
    user_id: int,
    actor: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
) -> None:
    target = db.get(User, user_id)
    if target is None or target.org_id != actor.org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )
    if target.id == actor.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate yourself.",
        )
    # Require at least one active admin remain in the org.
    if target.role == UserRole.admin.value and target.is_active:
        other_admins = db.scalar(
            select(User.id).where(
                User.org_id == actor.org_id,
                User.role == UserRole.admin.value,
                User.is_active.is_(True),
                User.id != target.id,
            )
        )
        if other_admins is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot deactivate the last active admin.",
            )
    target.is_active = False
    db.commit()


@router.get("/me", response_model=TeamMemberOut)
def me(user: User = Depends(get_current_user)) -> TeamMemberOut:
    return TeamMemberOut.model_validate(user)
