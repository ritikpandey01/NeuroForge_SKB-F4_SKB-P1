from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.supplier import Supplier


class SupplierSubmission(Base):
    __tablename__ = "supplier_submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_id: Mapped[int] = mapped_column(
        ForeignKey("suppliers.id", ondelete="CASCADE"), index=True
    )
    period: Mapped[str] = mapped_column(String(20))  # e.g. "2024-Q3"
    submitted_data: Mapped[dict] = mapped_column(JSON)
    data_quality_score: Mapped[int] = mapped_column(Integer, default=3)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    # pending / accepted / flagged / rejected
    submitted_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    supplier: Mapped["Supplier"] = relationship(back_populates="submissions")
