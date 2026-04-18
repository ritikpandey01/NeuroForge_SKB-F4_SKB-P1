from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.organization import Organization


class UserRole(str, Enum):
    admin = "admin"
    analyst = "analyst"
    viewer = "viewer"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False, default=UserRole.viewer.value)
    org_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="1"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    organization: Mapped["Organization"] = relationship(back_populates="users")
