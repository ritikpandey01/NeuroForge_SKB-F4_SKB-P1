from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.organization import Organization
    from app.db.models.supplier_submission import SupplierSubmission


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    industry: Mapped[str] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(100))
    contact_email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    tier: Mapped[int] = mapped_column(Integer)  # 1, 2, 3
    data_maturity_level: Mapped[str] = mapped_column(
        String(50)
    )  # spend_based / activity_based / verified_primary
    scope3_category: Mapped[str] = mapped_column(String(100))
    annual_spend: Mapped[float] = mapped_column(Float)  # INR crores
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    organization: Mapped["Organization"] = relationship(back_populates="suppliers")
    submissions: Mapped[list["SupplierSubmission"]] = relationship(
        back_populates="supplier", cascade="all, delete-orphan"
    )
