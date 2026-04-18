from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.emission import Emission
    from app.db.models.facility import Facility


class ActivityData(Base):
    __tablename__ = "activity_data"

    id: Mapped[int] = mapped_column(primary_key=True)
    facility_id: Mapped[int] = mapped_column(
        ForeignKey("facilities.id", ondelete="CASCADE"), index=True
    )
    scope: Mapped[int] = mapped_column(Integer, index=True)  # 1, 2, 3
    category: Mapped[str] = mapped_column(String(50), index=True)
    subcategory: Mapped[str] = mapped_column(String(100), index=True)
    activity_description: Mapped[str] = mapped_column(String(500))
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50))
    period_start: Mapped[date] = mapped_column(Date, index=True)
    period_end: Mapped[date] = mapped_column(Date)
    source_document: Mapped[str | None] = mapped_column(String(500), nullable=True)
    data_quality_score: Mapped[int] = mapped_column(Integer, default=3)  # 1-5
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    uploaded_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    department_head_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    department_head_email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    facility: Mapped["Facility"] = relationship(back_populates="activities")
    emissions: Mapped[list["Emission"]] = relationship(
        back_populates="activity", cascade="all, delete-orphan"
    )
