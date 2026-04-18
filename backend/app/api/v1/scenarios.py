"""Scenario simulator endpoints (Module 9).

Two-endpoint pattern, same as anomaly detection:
    - POST /scenarios/simulate   — pure math, always succeeds
    - POST /scenarios/narrative  — optional LLM pass, graceful 503/502

Keep these separate. The deterministic math must work without an API key;
the narrative is an optional second call.
"""

from __future__ import annotations

from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from openai import APIError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.core.config import settings
from app.core.llm_client import CircuitBreakerOpen, LLMNotConfigured, llm
from app.db.models import ActivityData, Emission, Facility, Organization, User, UserRole
from app.db.session import get_db
from app.schemas.scenario import (
    ExposurePointOut,
    LeverContributionOut,
    NarrativeRequest,
    NarrativeResponse,
    ScenarioRequest,
    ScenarioResponse,
    YearPointOut,
)
from app.services.scenario_engine import (
    DEFAULT_CARBON_PRICE_INR_PER_TONNE,
    PRESETS,
    Levers,
    simulate,
)

router = APIRouter(prefix="/scenarios")

KG_PER_TONNE = 1000.0


def _resolve_baseline(
    db: Session, year: int | None, *, org_id: int
) -> tuple[int, dict[int, float]]:
    """Return (baseline_year, scope_totals_tonnes) from the ledger.

    If `year` is None, use the latest calendar year that has any emissions.
    Scope totals default to 0 for any scope absent in the data."""
    year_filter = (
        select(func.max(func.strftime("%Y", ActivityData.period_start)))
        .join(Facility, ActivityData.facility_id == Facility.id)
        .where(Facility.org_id == org_id)
    )
    if year is None:
        latest = db.scalar(year_filter)
        if not latest:
            raise HTTPException(
                409,
                "No emissions in the ledger yet. Add activity data before running a scenario.",
            )
        year = int(latest)

    stmt = (
        select(Emission.scope, func.sum(Emission.co2e_kg))
        .join(ActivityData, Emission.activity_data_id == ActivityData.id)
        .join(Facility, ActivityData.facility_id == Facility.id)
        .where(Facility.org_id == org_id)
        .where(func.strftime("%Y", ActivityData.period_start) == f"{year:04d}")
        .group_by(Emission.scope)
    )
    rows = db.execute(stmt).all()
    totals: dict[int, float] = defaultdict(float)
    for scope, kg in rows:
        totals[scope] = float(kg or 0.0) / KG_PER_TONNE

    if not any(totals.values()):
        raise HTTPException(
            409,
            f"No emissions found for {year}. Try a different baseline year.",
        )
    return year, totals


@router.post("/simulate", response_model=ScenarioResponse)
def simulate_scenario(
    req: ScenarioRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin, UserRole.analyst)),
) -> ScenarioResponse:
    baseline_year, scope_totals = _resolve_baseline(
        db, req.baseline_year, org_id=user.org_id
    )

    lever_values = req.levers.model_dump()
    if req.preset:
        if req.preset not in PRESETS:
            raise HTTPException(422, f"unknown preset: {req.preset}")
        lever_values = PRESETS[req.preset]
    levers = Levers(**lever_values)

    # Resolve carbon price: explicit override → organization default → hardcoded default.
    if req.carbon_price_inr_per_tonne is not None:
        carbon_price = req.carbon_price_inr_per_tonne
    else:
        org = db.get(Organization, user.org_id)
        carbon_price = (
            org.carbon_price_inr_per_tonne if org else DEFAULT_CARBON_PRICE_INR_PER_TONNE
        )

    try:
        result = simulate(
            baseline_year=baseline_year,
            target_year=req.target_year,
            baseline_scope_1=scope_totals.get(1, 0.0),
            baseline_scope_2=scope_totals.get(2, 0.0),
            baseline_scope_3=scope_totals.get(3, 0.0),
            levers=levers,
            carbon_price_inr_per_tonne=carbon_price,
        )
    except ValueError as e:
        raise HTTPException(422, str(e)) from e

    return ScenarioResponse(
        baseline_year=result.baseline_year,
        target_year=result.target_year,
        baseline_total_tonnes=(
            scope_totals.get(1, 0.0) + scope_totals.get(2, 0.0) + scope_totals.get(3, 0.0)
        ),
        baseline_scope_1=scope_totals.get(1, 0.0),
        baseline_scope_2=scope_totals.get(2, 0.0),
        baseline_scope_3=scope_totals.get(3, 0.0),
        baseline=[YearPointOut(**p.__dict__) for p in result.baseline],
        scenario=[YearPointOut(**p.__dict__) for p in result.scenario],
        sbti=[YearPointOut(**p.__dict__) for p in result.sbti],
        lever_contributions=[
            LeverContributionOut(**c.__dict__) for c in result.lever_contributions
        ],
        scope_deltas_pct=result.scope_deltas,
        levers_applied=result.levers_applied,
        carbon_price_inr_per_tonne=result.carbon_price_inr_per_tonne,
        exposure_by_year=[
            ExposurePointOut(**e.__dict__) for e in result.exposure_by_year
        ],
        baseline_total_exposure_inr=result.baseline_total_exposure_inr,
        scenario_total_exposure_inr=result.scenario_total_exposure_inr,
        total_savings_inr=result.total_savings_inr,
    )


# ── Narrative (LLM, optional) ─────────────────────────────────────────


_SYSTEM_PROMPT = """You are a transition-plan analyst advising a corporate sustainability team.

You'll receive a decarbonization scenario: baseline year, target year, per-scope baseline tonnes CO2e, lever slider values (0-100), per-lever avoided tonnes at target year, and final scope deltas.

Write a 3-paragraph narrative (max ~220 words total):

1. Headline result — target-year total vs baseline, % reduction, whether it hits a 1.5°C-aligned ~4.2%/yr linear pathway.
2. Which 2-3 levers do the heaviest lifting and why, tied to the scope they target. Call out any lever that's cranked high but contributing little (scope it targets is small).
3. One concrete operational risk or dependency the team should plan for to realize this scenario (e.g. grid decarbonization assumptions, supplier data availability, capex phasing).

Plain prose, no bullets, no headings. Be direct. Use concrete numbers from the scenario."""


def _build_user_prompt(s: ScenarioResponse) -> str:
    contribs = "\n".join(
        f"  - {c.lever}: avoids {c.avoided_tonnes:,.0f} tCO2e ({c.pct_of_baseline:.1f}% of baseline)"
        for c in s.lever_contributions
    )
    deltas = ", ".join(f"{k}: {v:+.1f}%" for k, v in s.scope_deltas_pct.items())
    levers = ", ".join(f"{k}={v:.0f}" for k, v in s.levers_applied.items())
    return (
        f"Baseline year: {s.baseline_year}\n"
        f"Target year: {s.target_year}\n"
        f"Baseline total: {s.baseline_total_tonnes:,.0f} tCO2e "
        f"(S1 {s.baseline_scope_1:,.0f} · S2 {s.baseline_scope_2:,.0f} · "
        f"S3 {s.baseline_scope_3:,.0f})\n"
        f"Lever values: {levers}\n"
        f"Lever contributions at target year:\n{contribs}\n"
        f"Scope deltas vs baseline at target year: {deltas}\n"
        f"Target-year total under scenario: {s.scenario[-1].total:,.0f} tCO2e"
    )


@router.post("/narrative", response_model=NarrativeResponse)
def generate_narrative(
    req: NarrativeRequest,
    _user: User = Depends(require_role(UserRole.admin, UserRole.analyst)),
) -> NarrativeResponse:
    try:
        resp = llm.chat_completions_create(
            model=settings.OPENAI_MODEL,
            max_tokens=450,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_prompt(req.scenario)},
            ],
        )
    except LLMNotConfigured as e:
        raise HTTPException(503, str(e)) from e
    except CircuitBreakerOpen as e:
        raise HTTPException(503, str(e)) from e
    except APIError as e:
        raise HTTPException(502, getattr(e, "message", None) or str(e)) from e

    text = (resp.choices[0].message.content or "").strip()
    if not text:
        raise HTTPException(502, "LLM returned empty narrative.")

    return NarrativeResponse(narrative=text, model=settings.OPENAI_MODEL)
