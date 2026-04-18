from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.organization import Organization


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"))
    report_type: Mapped[str] = mapped_column(String(20))  # BRSR / GRI / TCFD / CDP
    period: Mapped[str] = mapped_column(String(20))  # e.g. "FY2024-25"
    generated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    # pending / generating / ready / failed

    organization: Mapped["Organization"] = relationship(back_populates="reports")
