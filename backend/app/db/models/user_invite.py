from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.organization import Organization


class UserInvite(Base):
    __tablename__ = "user_invites"

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    email: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False)
    # sha256 hex of the one-time token; the plaintext is only returned once to the inviter.
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    invited_by_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    organization: Mapped["Organization"] = relationship(back_populates="user_invites")
