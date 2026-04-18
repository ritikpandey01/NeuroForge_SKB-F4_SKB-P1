from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.audit_log import AuditLog
    from app.db.models.facility import Facility
    from app.db.models.report import Report
    from app.db.models.scenario import Scenario
    from app.db.models.supplier import Supplier
    from app.db.models.user import User
    from app.db.models.user_invite import UserInvite


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    industry: Mapped[str] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(100))
    base_year: Mapped[int] = mapped_column(Integer)
    net_zero_target_year: Mapped[int] = mapped_column(Integer)
    # Assumed carbon price for scenario financial exposure modeling.
    # Default ≈ ₹2000/tCO2e (~$24 USD), a plausible India CBAM-era internal price.
    carbon_price_inr_per_tonne: Mapped[float] = mapped_column(
        Float, nullable=False, default=2000.0, server_default="2000.0"
    )
    # 1–12. Default 4 = Indian fiscal year (April–March). BRSR tenants use 4;
    # GRI/TCFD tenants on a calendar year use 1. Drives period resolution in
    # reports and dashboards.
    fiscal_year_start_month: Mapped[int] = mapped_column(
        Integer, nullable=False, default=4, server_default="4"
    )
    # NULL until the first admin completes the onboarding wizard. RequireAuth
    # redirects to /onboarding while this is NULL.
    onboarding_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    facilities: Mapped[list["Facility"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    suppliers: Mapped[list["Supplier"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    scenarios: Mapped[list["Scenario"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    reports: Mapped[list["Report"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    users: Mapped[list["User"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    user_invites: Mapped[list["UserInvite"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
