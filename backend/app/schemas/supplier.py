from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

MaturityLevel = Literal["spend_based", "activity_based", "verified_primary"]


class SupplierBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    industry: str = Field(max_length=100)
    country: str = Field(max_length=100)
    contact_email: str | None = Field(default=None, max_length=200)
    tier: int = Field(ge=1, le=3)
    data_maturity_level: MaturityLevel
    scope3_category: str = Field(max_length=100)
    annual_spend: float = Field(ge=0)


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    industry: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)
    contact_email: str | None = Field(default=None, max_length=200)
    tier: int | None = Field(default=None, ge=1, le=3)
    data_maturity_level: MaturityLevel | None = None
    scope3_category: str | None = Field(default=None, max_length=100)
    annual_spend: float | None = Field(default=None, ge=0)


class SupplierOut(SupplierBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    org_id: int
    created_at: datetime
    submissions_count: int = 0
    latest_submission_status: str | None = None


# ── Impact matrix ──────────────────────────────────────────────────────

SpendBucket = Literal["low", "medium", "high"]


class MatrixCell(BaseModel):
    spend_bucket: SpendBucket
    data_maturity_level: MaturityLevel
    supplier_count: int
    total_spend: float  # INR crores
    supplier_ids: list[int]


class ImpactMatrixOut(BaseModel):
    spend_thresholds: dict[str, float]  # "low_max", "medium_max" — INR crores
    cells: list[MatrixCell]
    total_suppliers: int
    total_spend: float
