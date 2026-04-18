from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

LeverName = Literal[
    "renewable_electricity_share",
    "energy_efficiency_pct",
    "fleet_electrification",
    "supplier_engagement",
    "logistics_mode_shift",
]

PresetName = Literal["net_zero_2050", "sbti_1p5", "business_as_usual"]


class LeversIn(BaseModel):
    renewable_electricity_share: float = Field(0.0, ge=0, le=100)
    energy_efficiency_pct: float = Field(0.0, ge=0, le=100)
    fleet_electrification: float = Field(0.0, ge=0, le=100)
    supplier_engagement: float = Field(0.0, ge=0, le=100)
    logistics_mode_shift: float = Field(0.0, ge=0, le=100)


class ScenarioRequest(BaseModel):
    baseline_year: int | None = Field(
        default=None,
        description="Defaults to latest year with non-zero emissions in the DB.",
    )
    target_year: int = Field(2050, ge=2026, le=2100)
    levers: LeversIn = LeversIn()
    preset: PresetName | None = Field(
        default=None,
        description="If set, overrides `levers` with the named preset's values.",
    )
    carbon_price_inr_per_tonne: float | None = Field(
        default=None,
        ge=0,
        le=50000,
        description="Override org default. Null → use organization's configured price.",
    )


class YearPointOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    year: int
    scope_1: float
    scope_2: float
    scope_3: float
    total: float


class LeverContributionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    lever: str
    avoided_tonnes: float
    pct_of_baseline: float


class ExposurePointOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    year: int
    baseline_inr: float
    scenario_inr: float
    savings_inr: float


class ScenarioResponse(BaseModel):
    baseline_year: int
    target_year: int
    baseline_total_tonnes: float
    baseline_scope_1: float
    baseline_scope_2: float
    baseline_scope_3: float
    baseline: list[YearPointOut]
    scenario: list[YearPointOut]
    sbti: list[YearPointOut]
    lever_contributions: list[LeverContributionOut]
    scope_deltas_pct: dict[str, float]
    levers_applied: dict[str, float]
    # Carbon pricing overlay (Gap 2)
    carbon_price_inr_per_tonne: float
    exposure_by_year: list[ExposurePointOut]
    baseline_total_exposure_inr: float
    scenario_total_exposure_inr: float
    total_savings_inr: float


class NarrativeRequest(BaseModel):
    scenario: ScenarioResponse


class NarrativeResponse(BaseModel):
    narrative: str
    model: str
