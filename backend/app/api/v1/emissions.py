from collections import defaultdict
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.api.scoping import ensure_emission, ensure_facility
from app.db.models import ActivityData, Emission, EmissionFactor, Facility, User, UserRole
from app.db.session import get_db
from app.schemas.emission import (
    CalcRequest,
    CalcResponse,
    CategoryBreakdown,
    EmissionLedgerRow,
    EmissionsSummary,
    FacilityBreakdown,
    MethodologyOut,
    MonthlyPoint,
    ScopeBreakdown,
)
from app.services.calculation_engine import calculate_batch

router = APIRouter(prefix="/emissions")


KG_PER_TONNE = 1000.0


@router.post("/calculate", response_model=CalcResponse)
def calculate(
    req: CalcRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin, UserRole.analyst)),
) -> CalcResponse:
    if req.facility_id is not None:
        ensure_facility(db, req.facility_id, user.org_id)
    if req.activity_ids:
        # Reject any activity_id that isn't inside the caller's org — protects
        # against cross-tenant id guessing.
        owned_ids = set(
            db.scalars(
                select(ActivityData.id)
                .join(Facility, ActivityData.facility_id == Facility.id)
                .where(ActivityData.id.in_(req.activity_ids))
                .where(Facility.org_id == user.org_id)
            ).all()
        )
        if owned_ids != set(req.activity_ids):
            from fastapi import HTTPException

            raise HTTPException(404, "one or more activity_ids not found")

    result = calculate_batch(
        db,
        activity_ids=req.activity_ids,
        facility_id=req.facility_id,
        scope=req.scope,
        region_hint=req.region_hint,
        org_id=user.org_id,
    )
    db.commit()
    return CalcResponse(
        **result,
        total_co2e_tonnes=result["total_co2e_kg"] / KG_PER_TONNE,
    )


@router.get("", response_model=list[EmissionLedgerRow])
def list_emissions(
    scope: int | None = Query(None),
    facility_id: int | None = Query(None),
    period_start: date | None = Query(None),
    period_end: date | None = Query(None),
    limit: int = Query(500, le=5000),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[EmissionLedgerRow]:
    stmt = (
        select(Emission, ActivityData, Facility, EmissionFactor)
        .join(ActivityData, Emission.activity_data_id == ActivityData.id)
        .join(Facility, ActivityData.facility_id == Facility.id)
        .outerjoin(EmissionFactor, Emission.emission_factor_id == EmissionFactor.id)
        .where(Facility.org_id == user.org_id)
    )
    if scope:
        stmt = stmt.where(Emission.scope == scope)
    if facility_id:
        stmt = stmt.where(ActivityData.facility_id == facility_id)
    if period_start:
        stmt = stmt.where(ActivityData.period_start >= period_start)
    if period_end:
        stmt = stmt.where(ActivityData.period_end <= period_end)
    stmt = stmt.order_by(ActivityData.period_start.desc(), Emission.id.desc()).limit(limit)

    rows = db.execute(stmt).all()
    return [
        EmissionLedgerRow(
            id=em.id,
            activity_id=act.id,
            facility_id=fac.id,
            facility_name=fac.name,
            scope=em.scope,
            category=em.category,
            subcategory=act.subcategory,
            quantity=act.quantity,
            unit=act.unit,
            period_start=act.period_start,
            period_end=act.period_end,
            co2e_kg=em.co2e_kg,
            co2e_tonnes=em.co2e_kg / KG_PER_TONNE,
            calculation_method=em.calculation_method,
            factor_source=factor.source if factor else None,
            data_quality_score=act.data_quality_score,
            verified=act.verified,
        )
        for em, act, fac, factor in rows
    ]


@router.get("/summary", response_model=EmissionsSummary)
def summary(
    facility_id: int | None = Query(None),
    period_start: date | None = Query(None),
    period_end: date | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> EmissionsSummary:
    stmt = (
        select(Emission, ActivityData, Facility)
        .join(ActivityData, Emission.activity_data_id == ActivityData.id)
        .join(Facility, ActivityData.facility_id == Facility.id)
        .where(Facility.org_id == user.org_id)
    )

    if facility_id:
        stmt = stmt.where(ActivityData.facility_id == facility_id)
    if period_start:
        stmt = stmt.where(ActivityData.period_start >= period_start)
    if period_end:
        stmt = stmt.where(ActivityData.period_end <= period_end)

    rows = db.execute(stmt).all()

    total_kg = 0.0
    by_scope: dict[int, float] = defaultdict(float)
    by_cat: dict[tuple[int, str], float] = defaultdict(float)
    by_fac: dict[tuple[int, str], float] = defaultdict(float)
    by_month: dict[str, dict[int, float]] = defaultdict(lambda: {1: 0.0, 2: 0.0, 3: 0.0})

    verified = 0
    total_rows = 0

    for emission, activity, facility in rows:
        total_kg += emission.co2e_kg
        by_scope[emission.scope] += emission.co2e_kg
        by_cat[(emission.scope, emission.category)] += emission.co2e_kg
        by_fac[(facility.id, facility.name)] += emission.co2e_kg

        month_key = activity.period_start.strftime("%Y-%m")
        by_month[month_key][emission.scope] += emission.co2e_kg

        total_rows += 1
        if activity.verified:
            verified += 1

    total_t = total_kg / KG_PER_TONNE

    scope_breakdown = [
        ScopeBreakdown(
            scope=s,
            co2e_tonnes=by_scope[s] / KG_PER_TONNE,
            pct_of_total=(by_scope[s] / total_kg * 100) if total_kg else 0.0,
        )
        for s in sorted(by_scope)
    ]

    cat_breakdown = sorted(
        [
            CategoryBreakdown(scope=s, category=c, co2e_tonnes=v / KG_PER_TONNE)
            for (s, c), v in by_cat.items()
        ],
        key=lambda x: x.co2e_tonnes,
        reverse=True,
    )

    fac_breakdown = sorted(
        [
            FacilityBreakdown(facility_id=fid, facility_name=fname, co2e_tonnes=v / KG_PER_TONNE)
            for (fid, fname), v in by_fac.items()
        ],
        key=lambda x: x.co2e_tonnes,
        reverse=True,
    )

    monthly = [
        MonthlyPoint(
            period=k,
            scope_1=v[1] / KG_PER_TONNE,
            scope_2=v[2] / KG_PER_TONNE,
            scope_3=v[3] / KG_PER_TONNE,
            total=(v[1] + v[2] + v[3]) / KG_PER_TONNE,
        )
        for k, v in sorted(by_month.items())
    ]

    quality_pct = (verified / total_rows * 100) if total_rows else 0.0

    return EmissionsSummary(
        period_start=period_start,
        period_end=period_end,
        total_co2e_tonnes=total_t,
        by_scope=scope_breakdown,
        by_category=cat_breakdown,
        by_facility=fac_breakdown,
        monthly=monthly,
        data_quality_verified_pct=quality_pct,
    )


@router.get("/{emission_id}/methodology", response_model=MethodologyOut)
def methodology(
    emission_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MethodologyOut:
    ensure_emission(db, emission_id, user.org_id)
    row = db.execute(
        select(Emission, ActivityData, EmissionFactor)
        .join(ActivityData, Emission.activity_data_id == ActivityData.id)
        .outerjoin(EmissionFactor, Emission.emission_factor_id == EmissionFactor.id)
        .where(Emission.id == emission_id)
    ).first()

    emission, activity, factor = row
    return MethodologyOut(
        emission_id=emission.id,
        activity_id=activity.id,
        scope=emission.scope,
        category=activity.category,
        subcategory=activity.subcategory,
        activity_description=activity.activity_description,
        quantity=activity.quantity,
        unit=activity.unit,
        period_start=activity.period_start,
        period_end=activity.period_end,
        factor_id=factor.id if factor else None,
        factor_value=factor.factor_value if factor else None,
        factor_unit=factor.unit if factor else None,
        factor_source=factor.source if factor else None,
        factor_year=factor.year if factor else None,
        co2e_kg=emission.co2e_kg,
        co2e_tonnes=emission.co2e_kg / KG_PER_TONNE,
        calculation_method=emission.calculation_method,
        data_quality_score=activity.data_quality_score,
        verified=activity.verified,
    )
