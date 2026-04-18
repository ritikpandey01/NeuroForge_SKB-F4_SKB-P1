from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.organization import Organization


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    user: Mapped[str] = mapped_column(String(100))
    action: Mapped[str] = mapped_column(String(50))  # create / update / delete
    entity_type: Mapped[str] = mapped_column(String(50), index=True)
    entity_id: Mapped[int] = mapped_column(Integer)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    organization: Mapped["Organization"] = relationship(back_populates="audit_logs")
