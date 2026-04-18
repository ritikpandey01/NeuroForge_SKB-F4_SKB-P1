"""Governance dashboards — pre-composed views for two personas (Module 11)."""

from __future__ import annotations

from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import (
    ActivityData,
    AnomalyDetection,
    Emission,
    Facility,
    Organization,
    Report,
    Supplier,
    SupplierSubmission,
    User,
)
from app.db.session import get_db
from app.schemas.dashboard import (
    ExecutiveDashboard,
    FacilityTile,
    OperationsDashboard,
    RiskItem,
    ScopeMixItem,
    SupplierCompliance,
)

router = APIRouter(prefix="/dashboards")

KG_PER_TONNE = 1000.0
SBTI_ANNUAL_REDUCTION = 0.042


def _org(db: Session, org_id: int) -> Organization:
    org = db.get(Organization, org_id)
    if not org:
        raise HTTPException(500, f"organization {org_id} not found")
    return org


def _latest_year_with_data(db: Session, org_id: int) -> int:
    latest = db.scalar(
        select(func.max(func.strftime("%Y", ActivityData.period_start)))
        .join(Facility, ActivityData.facility_id == Facility.id)
        .where(Facility.org_id == org_id)
    )
    if not latest:
        raise HTTPException(
            409, "No emissions in the ledger yet. Add activity data before loading dashboards."
        )
    return int(latest)


def _totals_for_year(
    db: Session, year: int, *, org_id: int
) -> tuple[float, dict[int, float]]:
    """(total_tonnes, by_scope_tonnes) for a calendar year."""
    rows = db.execute(
        select(Emission.scope, func.sum(Emission.co2e_kg))
        .join(ActivityData, Emission.activity_data_id == ActivityData.id)
        .join(Facility, ActivityData.facility_id == Facility.id)
        .where(Facility.org_id == org_id)
        .where(func.strftime("%Y", ActivityData.period_start) == f"{year:04d}")
        .group_by(Emission.scope)
    ).all()
    by_scope: dict[int, float] = defaultdict(float)
    total_kg = 0.0
    for scope, kg in rows:
        kg = float(kg or 0.0)
        by_scope[scope] = kg / KG_PER_TONNE
        total_kg += kg
    return total_kg / KG_PER_TONNE, by_scope


# ── Executive ─────────────────────────────────────────────────────────


@router.get("/executive", response_model=ExecutiveDashboard)
def executive(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ExecutiveDashboard:
    org = _org(db, user.org_id)
    current_year = _latest_year_with_data(db, user.org_id)
    prior_year = current_year - 1

    current_total, current_by_scope = _totals_for_year(db, current_year, org_id=user.org_id)
    prior_total, _ = _totals_for_year(db, prior_year, org_id=user.org_id)

    base_year = org.base_year
    base_total, _ = _totals_for_year(db, base_year, org_id=user.org_id)
    if base_total == 0:
        base_total = prior_total or current_total

    years_elapsed = max(0, current_year - base_year)
    pathway_mult = max(0.0, 1.0 - SBTI_ANNUAL_REDUCTION * years_elapsed)
    sbti_target = base_total * pathway_mult
    sbti_gap = current_total - sbti_target

    yoy_delta = 0.0 if prior_total == 0 else (current_total - prior_total) / prior_total * 100.0

    scope_mix = [
        ScopeMixItem(
            scope=s,
            tonnes=current_by_scope.get(s, 0.0),
            pct=(current_by_scope.get(s, 0.0) / current_total * 100.0) if current_total else 0.0,
        )
        for s in sorted(current_by_scope)
    ]

    severity_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    risk_rows = list(
        db.scalars(
            select(AnomalyDetection)
            .where(AnomalyDetection.org_id == user.org_id)
            .where(
                AnomalyDetection.status.in_(("new", "acknowledged")),
                AnomalyDetection.severity.in_(("critical", "high")),
            )
            .order_by(AnomalyDetection.detected_at.desc())
            .limit(20)
        ).all()
    )
    risk_rows.sort(
        key=lambda r: (severity_rank.get(r.severity, 99), -r.detected_at.timestamp())
    )
    top_risks = [RiskItem.model_validate(r) for r in risk_rows[:3]]

    open_count = db.scalar(
        select(func.count(AnomalyDetection.id))
        .where(AnomalyDetection.org_id == user.org_id)
        .where(AnomalyDetection.status.in_(("new", "acknowledged")))
    ) or 0
    escalated_count = db.scalar(
        select(func.count(AnomalyDetection.id))
        .where(AnomalyDetection.org_id == user.org_id)
        .where(AnomalyDetection.escalation_status == "escalated")
    ) or 0
    board_reviewed_count = db.scalar(
        select(func.count(AnomalyDetection.id))
        .where(AnomalyDetection.org_id == user.org_id)
        .where(AnomalyDetection.escalation_status == "board_reviewed")
    ) or 0
    reports_count = db.scalar(
        select(func.count(Report.id)).where(Report.org_id == user.org_id)
    ) or 0

    carbon_price = float(org.carbon_price_inr_per_tonne or 0.0)
    carbon_exposure = current_total * carbon_price

    return ExecutiveDashboard(
        org_name=org.name,
        current_year=current_year,
        prior_year=prior_year,
        current_total_tonnes=current_total,
        prior_total_tonnes=prior_total,
        yoy_delta_pct=yoy_delta,
        scope_mix=scope_mix,
        base_year=base_year,
        base_year_total_tonnes=base_total,
        sbti_pathway_target_tonnes=sbti_target,
        sbti_gap_tonnes=sbti_gap,
        net_zero_target_year=org.net_zero_target_year,
        top_risks=top_risks,
        reports_generated=reports_count,
        anomalies_open=open_count,
        anomalies_escalated=escalated_count,
        anomalies_board_reviewed=board_reviewed_count,
        carbon_price_inr_per_tonne=carbon_price,
        carbon_exposure_current_inr=carbon_exposure,
    )


# ── Operations ────────────────────────────────────────────────────────


def _current_quarter(year: int, month: int) -> str:
    q = (month - 1) // 3 + 1
    return f"{year}-Q{q}"


@router.get("/operations", response_model=OperationsDashboard)
def operations(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OperationsDashboard:
    org = _org(db, user.org_id)
    current_year = _latest_year_with_data(db, user.org_id)
    prior_year = current_year - 1

    fac_totals = dict(
        db.execute(
            select(ActivityData.facility_id, func.sum(Emission.co2e_kg))
            .join(Emission, Emission.activity_data_id == ActivityData.id)
            .join(Facility, ActivityData.facility_id == Facility.id)
            .where(Facility.org_id == user.org_id)
            .where(func.strftime("%Y", ActivityData.period_start) == f"{current_year:04d}")
            .group_by(ActivityData.facility_id)
        ).all()
    )
    org_total_kg = sum(fac_totals.values()) or 0.0

    fac_activity = {
        row[0]: (row[1], row[2])
        for row in db.execute(
            select(
                ActivityData.facility_id,
                func.count(ActivityData.id),
                func.sum(func.iif(ActivityData.verified, 1, 0)),
            )
            .join(Facility, ActivityData.facility_id == Facility.id)
            .where(Facility.org_id == user.org_id)
            .where(func.strftime("%Y", ActivityData.period_start) == f"{current_year:04d}")
            .group_by(ActivityData.facility_id)
        ).all()
    }

    anom_rows = db.execute(
        select(AnomalyDetection.facility_id, func.count(AnomalyDetection.id))
        .where(AnomalyDetection.org_id == user.org_id)
        .where(
            AnomalyDetection.status.in_(("new", "acknowledged")),
            AnomalyDetection.facility_id.is_not(None),
        )
        .group_by(AnomalyDetection.facility_id)
    ).all()
    anom_by_fac = {fid: cnt for fid, cnt in anom_rows}

    facilities = list(db.scalars(select(Facility).where(Facility.org_id == org.id)).all())
    tiles: list[FacilityTile] = []
    for f in facilities:
        total_kg = float(fac_totals.get(f.id, 0.0) or 0.0)
        cnt, verified_cnt = fac_activity.get(f.id, (0, 0))
        cnt = int(cnt or 0)
        verified_cnt = int(verified_cnt or 0)
        dq = (verified_cnt / cnt * 100.0) if cnt else 0.0
        tiles.append(
            FacilityTile(
                facility_id=f.id,
                name=f.name,
                location=f.location,
                total_tonnes=total_kg / KG_PER_TONNE,
                pct_of_total=(total_kg / org_total_kg * 100.0) if org_total_kg else 0.0,
                data_quality_pct=dq,
                open_anomaly_count=int(anom_by_fac.get(f.id, 0)),
                activity_row_count=cnt,
            )
        )
    tiles.sort(key=lambda t: t.total_tonnes, reverse=True)

    rows_current = (
        db.scalar(
            select(func.count(ActivityData.id))
            .join(Facility, ActivityData.facility_id == Facility.id)
            .where(Facility.org_id == user.org_id)
            .where(func.strftime("%Y", ActivityData.period_start) == f"{current_year:04d}")
        )
        or 0
    )
    rows_prior = (
        db.scalar(
            select(func.count(ActivityData.id))
            .join(Facility, ActivityData.facility_id == Facility.id)
            .where(Facility.org_id == user.org_id)
            .where(func.strftime("%Y", ActivityData.period_start) == f"{prior_year:04d}")
        )
        or 0
    )

    latest_sub_period = db.scalar(
        select(func.max(SupplierSubmission.period))
        .join(Supplier, SupplierSubmission.supplier_id == Supplier.id)
        .where(Supplier.org_id == user.org_id)
    )
    current_q = latest_sub_period or _current_quarter(current_year, 12)
    total_suppliers = db.scalar(
        select(func.count(Supplier.id)).where(Supplier.org_id == user.org_id)
    ) or 0
    submissions_received = (
        db.scalar(
            select(func.count(func.distinct(SupplierSubmission.supplier_id)))
            .join(Supplier, SupplierSubmission.supplier_id == Supplier.id)
            .where(Supplier.org_id == user.org_id)
            .where(and_(SupplierSubmission.period == current_q))
        )
        or 0
    )
    compliance_pct = (submissions_received / total_suppliers * 100.0) if total_suppliers else 0.0

    return OperationsDashboard(
        current_year=current_year,
        activity_rows_this_period=rows_current,
        activity_rows_prior_period=rows_prior,
        facilities=tiles,
        supplier_compliance=SupplierCompliance(
            total_suppliers=total_suppliers,
            current_quarter=current_q,
            submissions_received=submissions_received,
            compliance_pct=compliance_pct,
        ),
    )
