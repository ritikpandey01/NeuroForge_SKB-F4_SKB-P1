from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class EmissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    activity_data_id: int
    scope: int
    category: str
    co2e_kg: float
    calculation_method: str
    emission_factor_id: int | None = None
    created_at: datetime


class EmissionLedgerRow(BaseModel):
    id: int
    activity_id: int
    facility_id: int
    facility_name: str
    scope: int
    category: str
    subcategory: str
    quantity: float
    unit: str
    period_start: date
    period_end: date
    co2e_kg: float
    co2e_tonnes: float
    calculation_method: str
    factor_source: str | None
    data_quality_score: int
    verified: bool


class CalcRequest(BaseModel):
    activity_ids: list[int] | None = None
    facility_id: int | None = None
    scope: int | None = None
    region_hint: str = "IN"


class CalcResponse(BaseModel):
    activities_seen: int
    computed: int
    already_had_emission: int
    errors: list[dict]
    total_co2e_kg: float
    total_co2e_tonnes: float


class ScopeBreakdown(BaseModel):
    scope: int
    co2e_tonnes: float
    pct_of_total: float


class CategoryBreakdown(BaseModel):
    category: str
    scope: int
    co2e_tonnes: float


class FacilityBreakdown(BaseModel):
    facility_id: int
    facility_name: str
    co2e_tonnes: float


class MonthlyPoint(BaseModel):
    period: str  # YYYY-MM
    scope_1: float
    scope_2: float
    scope_3: float
    total: float


class EmissionsSummary(BaseModel):
    period_start: date | None
    period_end: date | None
    total_co2e_tonnes: float
    by_scope: list[ScopeBreakdown]
    by_category: list[CategoryBreakdown]
    by_facility: list[FacilityBreakdown]
    monthly: list[MonthlyPoint]
    data_quality_verified_pct: float


class MethodologyOut(BaseModel):
    emission_id: int
    activity_id: int
    scope: int
    category: str
    subcategory: str
    activity_description: str
    quantity: float
    unit: str
    period_start: date
    period_end: date
    factor_id: int | None
    factor_value: float | None
    factor_unit: str | None
    factor_source: str | None
    factor_year: int | None
    co2e_kg: float
    co2e_tonnes: float
    calculation_method: str
    data_quality_score: int
    verified: bool
