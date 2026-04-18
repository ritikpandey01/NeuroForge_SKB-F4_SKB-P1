from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.activity_data import ActivityData
    from app.db.models.organization import Organization


class Facility(Base):
    __tablename__ = "facilities"

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(String(50))  # factory / office / warehouse
    location: Mapped[str] = mapped_column(String(200))
    country: Mapped[str] = mapped_column(String(100))
    default_department_head_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    default_department_head_email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    organization: Mapped["Organization"] = relationship(back_populates="facilities")
    activities: Mapped[list["ActivityData"]] = relationship(
        back_populates="facility", cascade="all, delete-orphan"
    )
