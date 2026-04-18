from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EmissionFactor(Base):
    __tablename__ = "emission_factors"

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(50), index=True)
    subcategory: Mapped[str] = mapped_column(String(100), index=True)
    factor_value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50))  # e.g. "kgCO2e/kWh"
    source: Mapped[str] = mapped_column(String(50))  # DEFRA/EPA/IPCC/CEA
    region: Mapped[str] = mapped_column(String(20), index=True)  # IN/US/UK/GLOBAL
    year: Mapped[int] = mapped_column(Integer)
