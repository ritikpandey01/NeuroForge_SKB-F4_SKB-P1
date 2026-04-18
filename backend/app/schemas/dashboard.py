from pydantic import BaseModel, ConfigDict


class ScopeMixItem(BaseModel):
    scope: int
    tonnes: float
    pct: float


class RiskItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    detector: str
    severity: str
    title: str
    facility_id: int | None


class ExecutiveDashboard(BaseModel):
    org_name: str
    current_year: int
    prior_year: int
    current_total_tonnes: float
    prior_total_tonnes: float
    yoy_delta_pct: float
    scope_mix: list[ScopeMixItem]
    base_year: int
    base_year_total_tonnes: float
    sbti_pathway_target_tonnes: float  # where we should be this year (4.2%/yr from base)
    sbti_gap_tonnes: float  # current - target; positive = over budget
    net_zero_target_year: int
    top_risks: list[RiskItem]
    reports_generated: int
    anomalies_open: int
    anomalies_escalated: int
    anomalies_board_reviewed: int
    # Carbon pricing exposure (Gap 2) — current_total × org price
    carbon_price_inr_per_tonne: float
    carbon_exposure_current_inr: float


class FacilityTile(BaseModel):
    facility_id: int
    name: str
    location: str
    total_tonnes: float
    pct_of_total: float
    data_quality_pct: float
    open_anomaly_count: int
    activity_row_count: int


class SupplierCompliance(BaseModel):
    total_suppliers: int
    current_quarter: str  # e.g. "2025-Q4"
    submissions_received: int
    compliance_pct: float


class OperationsDashboard(BaseModel):
    current_year: int
    activity_rows_this_period: int
    activity_rows_prior_period: int
    facilities: list[FacilityTile]
    supplier_compliance: SupplierCompliance
