from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.organization import Organization


class Scenario(Base):
    __tablename__ = "scenarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    parameters: Mapped[dict] = mapped_column(JSON)
    baseline_emissions: Mapped[float] = mapped_column(Float)
    projected_emissions: Mapped[float] = mapped_column(Float)
    created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    organization: Mapped["Organization"] = relationship(back_populates="scenarios")
