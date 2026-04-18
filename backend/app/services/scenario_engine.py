"""Scenario simulator — pure, deterministic trajectory math (Module 9).

Takes a baseline year's scope totals + five lever values (0–100% sliders) and
projects a yearly trajectory from baseline to target year. No DB writes, no
LLM calls — this module is unit-testable without fixtures.

Lever semantics (keep these in sync with the UI labels):

    1. renewable_electricity_share    — 0–100%: at 100%, removes up to 95% of
       Scope 2 electricity emissions. (Residual 5% reflects non-substitutable
       grid slivers, backup power, and Scope 2 categories that aren't pure
       electricity e.g. steam/heat.)

    2. energy_efficiency_pct          — 0–100%: at 100%, removes up to 30% of
       BOTH Scope 1 fuel use AND Scope 2 electricity. (Industry-typical ceiling
       for demand-side efficiency without process change.)

    3. fleet_electrification          — 0–100%: at 100%, removes up to 50% of
       Scope 1 emissions. (Assumes roughly half of S1 is mobile combustion —
       the rest is process emissions, stationary DG, refrigerants.)

    4. supplier_engagement            — 0–100%: at 100%, removes up to 40% of
       Scope 3 emissions. (Ceiling reflects that Cat-1 purchased goods is the
       dominant S3 slice but not all of it; supplier-specific factors realize
       30–40% reductions vs spend-based defaults.)

    5. logistics_mode_shift           — 0–100%: at 100%, removes up to 30% of
       Scope 3 emissions. (Road → rail for Cat-4 transportation; caps at the
       fraction of S3 that is actually transport.)

Effects compose multiplicatively within a scope — e.g. Scope 2 gets
(1 - renewable_eff) × (1 - efficiency_eff). Lever effects ramp linearly from
0 at baseline year to full value at target year — no S-curves, no discounting.
Keep it simple enough to explain in two sentences to a reviewer.

SBTi 1.5°C reference pathway: 4.2%/yr linear reduction of the baseline,
flat line on the chart for comparison (not an input).
"""

from __future__ import annotations

from dataclasses import dataclass, field

DEFAULT_CARBON_PRICE_INR_PER_TONNE = 2000.0


# Max reduction each lever can apply to each affected scope when the slider
# is at 100%. Tuple-of-(scope, fraction). Documented above.
LEVER_EFFECTS: dict[str, list[tuple[int, float]]] = {
    "renewable_electricity_share": [(2, 0.95)],
    "energy_efficiency_pct": [(1, 0.30), (2, 0.30)],
    "fleet_electrification": [(1, 0.50)],
    "supplier_engagement": [(3, 0.40)],
    "logistics_mode_shift": [(3, 0.30)],
}

SBTI_ANNUAL_REDUCTION = 0.042  # 4.2%/yr linear, 1.5°C-aligned


@dataclass
class Levers:
    renewable_electricity_share: float = 0.0
    energy_efficiency_pct: float = 0.0
    fleet_electrification: float = 0.0
    supplier_engagement: float = 0.0
    logistics_mode_shift: float = 0.0

    def as_dict(self) -> dict[str, float]:
        return {
            "renewable_electricity_share": self.renewable_electricity_share,
            "energy_efficiency_pct": self.energy_efficiency_pct,
            "fleet_electrification": self.fleet_electrification,
            "supplier_engagement": self.supplier_engagement,
            "logistics_mode_shift": self.logistics_mode_shift,
        }


@dataclass
class YearPoint:
    year: int
    scope_1: float
    scope_2: float
    scope_3: float
    total: float


@dataclass
class LeverContribution:
    lever: str
    avoided_tonnes: float  # at target year, relative to baseline flat line
    pct_of_baseline: float


@dataclass
class ExposurePoint:
    year: int
    baseline_inr: float
    scenario_inr: float
    savings_inr: float


@dataclass
class ScenarioResult:
    baseline_year: int
    target_year: int
    baseline: list[YearPoint]       # flat line at baseline totals
    scenario: list[YearPoint]       # lever-reduced trajectory
    sbti: list[YearPoint]           # 1.5°C reference pathway
    lever_contributions: list[LeverContribution]
    scope_deltas: dict[str, float]  # keys: scope_1, scope_2, scope_3, total — % change vs baseline at target year
    levers_applied: dict[str, float]
    # Carbon pricing overlay (Gap 2) — financial exposure = emitted tonnes ×
    # assumed price. Not a discounted NPV, just an annual × cumulative view.
    carbon_price_inr_per_tonne: float = 0.0
    exposure_by_year: list[ExposurePoint] = field(default_factory=list)
    baseline_total_exposure_inr: float = 0.0
    scenario_total_exposure_inr: float = 0.0
    total_savings_inr: float = 0.0


def _clamp01(x: float) -> float:
    if x < 0:
        return 0.0
    if x > 1:
        return 1.0
    return x


def _scope_factor(levers: Levers, scope: int, ramp: float) -> float:
    """Multiplicative factor in [0, 1] applied to this scope's baseline at
    a given ramp progress. Each lever that targets the scope contributes a
    `(1 - slider% * max_effect * ramp)` term."""
    levers_d = levers.as_dict()
    factor = 1.0
    for lever_name, effects in LEVER_EFFECTS.items():
        slider = _clamp01(levers_d[lever_name] / 100.0)
        for affected_scope, max_effect in effects:
            if affected_scope != scope:
                continue
            factor *= 1.0 - slider * max_effect * ramp
    return factor


def simulate(
    *,
    baseline_year: int,
    target_year: int,
    baseline_scope_1: float,
    baseline_scope_2: float,
    baseline_scope_3: float,
    levers: Levers,
    carbon_price_inr_per_tonne: float = DEFAULT_CARBON_PRICE_INR_PER_TONNE,
) -> ScenarioResult:
    """Project a yearly trajectory from `baseline_year` to `target_year`.

    All three emissions inputs are tonnes CO2e. Pure function — no DB or
    network calls. Raises `ValueError` if the year range is degenerate.
    """
    if target_year <= baseline_year:
        raise ValueError(
            f"target_year ({target_year}) must be strictly after baseline_year ({baseline_year})"
        )

    baseline_total = baseline_scope_1 + baseline_scope_2 + baseline_scope_3
    years = list(range(baseline_year, target_year + 1))

    baseline_pts: list[YearPoint] = []
    scenario_pts: list[YearPoint] = []
    sbti_pts: list[YearPoint] = []

    span = target_year - baseline_year
    for y in years:
        ramp = (y - baseline_year) / span  # 0 .. 1

        s1 = baseline_scope_1 * _scope_factor(levers, 1, ramp)
        s2 = baseline_scope_2 * _scope_factor(levers, 2, ramp)
        s3 = baseline_scope_3 * _scope_factor(levers, 3, ramp)
        scenario_pts.append(YearPoint(y, s1, s2, s3, s1 + s2 + s3))

        baseline_pts.append(
            YearPoint(y, baseline_scope_1, baseline_scope_2, baseline_scope_3, baseline_total)
        )

        # SBTi: 4.2%/yr linear on the baseline total. Scope-level split is
        # proportional — we don't claim a scope-specific SBTi, just the
        # overall pathway for chart comparison.
        sbti_mult = max(0.0, 1.0 - SBTI_ANNUAL_REDUCTION * (y - baseline_year))
        sbti_pts.append(
            YearPoint(
                y,
                baseline_scope_1 * sbti_mult,
                baseline_scope_2 * sbti_mult,
                baseline_scope_3 * sbti_mult,
                baseline_total * sbti_mult,
            )
        )

    # Lever contributions at target year. Computed by turning every *other*
    # lever off and measuring the drop this one alone produces — a leave-one-in
    # attribution that avoids over-counting when levers target the same scope.
    contributions = _lever_contributions(
        levers=levers,
        baseline_scope_1=baseline_scope_1,
        baseline_scope_2=baseline_scope_2,
        baseline_scope_3=baseline_scope_3,
    )

    target_pt = scenario_pts[-1]
    deltas = {
        "scope_1": _pct_delta(baseline_scope_1, target_pt.scope_1),
        "scope_2": _pct_delta(baseline_scope_2, target_pt.scope_2),
        "scope_3": _pct_delta(baseline_scope_3, target_pt.scope_3),
        "total": _pct_delta(baseline_total, target_pt.total),
    }

    # Carbon pricing overlay (skip year 0 — that's the baseline, no delta yet).
    price = max(0.0, carbon_price_inr_per_tonne)
    exposure_pts: list[ExposurePoint] = []
    baseline_total_exposure = 0.0
    scenario_total_exposure = 0.0
    for bp, sp in zip(baseline_pts, scenario_pts):
        b_inr = bp.total * price
        s_inr = sp.total * price
        exposure_pts.append(
            ExposurePoint(
                year=bp.year,
                baseline_inr=b_inr,
                scenario_inr=s_inr,
                savings_inr=b_inr - s_inr,
            )
        )
        baseline_total_exposure += b_inr
        scenario_total_exposure += s_inr

    return ScenarioResult(
        baseline_year=baseline_year,
        target_year=target_year,
        baseline=baseline_pts,
        scenario=scenario_pts,
        sbti=sbti_pts,
        lever_contributions=contributions,
        scope_deltas=deltas,
        levers_applied=levers.as_dict(),
        carbon_price_inr_per_tonne=price,
        exposure_by_year=exposure_pts,
        baseline_total_exposure_inr=baseline_total_exposure,
        scenario_total_exposure_inr=scenario_total_exposure,
        total_savings_inr=baseline_total_exposure - scenario_total_exposure,
    )


def _pct_delta(before: float, after: float) -> float:
    if before == 0:
        return 0.0
    return (after - before) / before * 100.0


def _lever_contributions(
    *,
    levers: Levers,
    baseline_scope_1: float,
    baseline_scope_2: float,
    baseline_scope_3: float,
) -> list[LeverContribution]:
    """Leave-one-in attribution at full ramp (target year). For each lever,
    simulate the trajectory with only that lever active and measure the
    avoided tonnes at ramp=1. This avoids the additivity issue when two
    levers target the same scope — e.g. both 'renewables' and 'efficiency'
    affect Scope 2, and naive summing would double-count their overlap."""
    total_baseline = baseline_scope_1 + baseline_scope_2 + baseline_scope_3
    out: list[LeverContribution] = []
    for name in LEVER_EFFECTS:
        solo_levers = Levers()
        setattr(solo_levers, name, getattr(levers, name))
        s1 = baseline_scope_1 * _scope_factor(solo_levers, 1, 1.0)
        s2 = baseline_scope_2 * _scope_factor(solo_levers, 2, 1.0)
        s3 = baseline_scope_3 * _scope_factor(solo_levers, 3, 1.0)
        avoided = total_baseline - (s1 + s2 + s3)
        out.append(
            LeverContribution(
                lever=name,
                avoided_tonnes=avoided,
                pct_of_baseline=(avoided / total_baseline * 100.0) if total_baseline else 0.0,
            )
        )
    return out


# ── Presets ───────────────────────────────────────────────────────────


PRESETS: dict[str, dict[str, float]] = {
    "net_zero_2050": {
        # Aggressive on every lever — the ambition case.
        "renewable_electricity_share": 100.0,
        "energy_efficiency_pct": 80.0,
        "fleet_electrification": 90.0,
        "supplier_engagement": 80.0,
        "logistics_mode_shift": 60.0,
    },
    "sbti_1p5": {
        # Tuned to roughly match the 4.2%/yr SBTi pathway at target year —
        # not a precise fit, just a sensible starting point for the slider UI.
        "renewable_electricity_share": 70.0,
        "energy_efficiency_pct": 50.0,
        "fleet_electrification": 60.0,
        "supplier_engagement": 50.0,
        "logistics_mode_shift": 40.0,
    },
    "business_as_usual": {
        "renewable_electricity_share": 0.0,
        "energy_efficiency_pct": 0.0,
        "fleet_electrification": 0.0,
        "supplier_engagement": 0.0,
        "logistics_mode_shift": 0.0,
    },
}
