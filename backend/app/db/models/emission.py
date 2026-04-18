from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.activity_data import ActivityData
    from app.db.models.emission_factor import EmissionFactor


class Emission(Base):
    __tablename__ = "emissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    activity_data_id: Mapped[int] = mapped_column(
        ForeignKey("activity_data.id", ondelete="CASCADE"), index=True
    )
    scope: Mapped[int] = mapped_column(Integer, index=True)
    category: Mapped[str] = mapped_column(String(50), index=True)
    co2e_kg: Mapped[float] = mapped_column(Float, nullable=False)
    calculation_method: Mapped[str] = mapped_column(String(500))
    emission_factor_id: Mapped[int | None] = mapped_column(
        ForeignKey("emission_factors.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    activity: Mapped["ActivityData"] = relationship(back_populates="emissions")
    factor: Mapped["EmissionFactor | None"] = relationship()
