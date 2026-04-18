"""Anomaly feed — list, scan, explain, acknowledge (Module 8)."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.api.scoping import ensure_anomaly
from app.db.models import AnomalyDetection, User, UserRole
from app.db.session import get_db
from app.schemas.anomaly import (
    AnomalyOut,
    AnomalyStatusUpdate,
    BoardReviewRequest,
    EscalationRequest,
    ExplainResponse,
    ScanResponse,
)
from app.services.anomaly_detector import explain_pending, run_scan
from app.services.audit import write_audit

router = APIRouter(prefix="/anomalies")


@router.get("", response_model=list[AnomalyOut])
def list_anomalies(
    severity: str | None = Query(None),
    status: str | None = Query(None),
    detector: str | None = Query(None),
    facility_id: int | None = Query(None),
    escalation_status: str | None = Query(
        None,
        description="Filter by escalation_status ('escalated', 'board_reviewed'); 'any' matches both",
    ),
    limit: int = Query(200, le=1000),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[AnomalyDetection]:
    stmt = (
        select(AnomalyDetection)
        .where(AnomalyDetection.org_id == user.org_id)
        .order_by(
            AnomalyDetection.severity,
            AnomalyDetection.detected_at.desc(),
        )
    )
    if severity:
        stmt = stmt.where(AnomalyDetection.severity == severity)
    if status:
        stmt = stmt.where(AnomalyDetection.status == status)
    if detector:
        stmt = stmt.where(AnomalyDetection.detector == detector)
    if facility_id:
        stmt = stmt.where(AnomalyDetection.facility_id == facility_id)
    if escalation_status:
        if escalation_status == "any":
            stmt = stmt.where(AnomalyDetection.escalation_status.is_not(None))
        else:
            stmt = stmt.where(AnomalyDetection.escalation_status == escalation_status)
    stmt = stmt.limit(limit)

    rows = list(db.scalars(stmt).all())
    rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    rows.sort(key=lambda r: (rank.get(r.severity, 99), -r.detected_at.timestamp()))
    return rows


@router.get("/summary")
def summary(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """Counts by severity + status, for the nav badge and Anomalies hero."""
    base = select(AnomalyDetection).where(AnomalyDetection.org_id == user.org_id)

    by_sev = dict(
        db.execute(
            select(AnomalyDetection.severity, func.count(AnomalyDetection.id))
            .where(AnomalyDetection.org_id == user.org_id)
            .group_by(AnomalyDetection.severity)
        ).all()
    )
    by_status = dict(
        db.execute(
            select(AnomalyDetection.status, func.count(AnomalyDetection.id))
            .where(AnomalyDetection.org_id == user.org_id)
            .group_by(AnomalyDetection.status)
        ).all()
    )
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
    return {
        "by_severity": by_sev,
        "by_status": by_status,
        "open_count": open_count,
        "escalated_count": escalated_count,
        "board_reviewed_count": board_reviewed_count,
    }


@router.post("/scan", response_model=ScanResponse)
def scan(
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin, UserRole.analyst)),
) -> ScanResponse:
    """Trigger a full statistical sweep. Idempotent (dedupe by fingerprint)."""
    result = run_scan(db, user.org_id)
    return ScanResponse(**result)


@router.post("/explain", response_model=ExplainResponse)
def explain(
    limit: int = Query(20, le=50),
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin, UserRole.analyst)),
) -> ExplainResponse:
    """Generate LLM explanations for anomalies that don't have one yet.
    Returns {explained, attempted, skipped_reason} — skipped_reason is set
    when the key is unset or the circuit is open."""
    return ExplainResponse(**explain_pending(db, org_id=user.org_id, limit=limit))


@router.patch("/{anomaly_id}", response_model=AnomalyOut)
def update_status(
    anomaly_id: int,
    payload: AnomalyStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin, UserRole.analyst)),
) -> AnomalyDetection:
    row = ensure_anomaly(db, anomaly_id, user.org_id)
    old_status = row.status
    row.status = payload.status
    if payload.status in ("acknowledged", "dismissed", "resolved"):
        row.acknowledged_at = datetime.utcnow()
        row.acknowledged_by = payload.acknowledged_by or user.email
    write_audit(
        db,
        user=user.email,
        org_id=user.org_id,
        action=payload.status,
        entity_type="anomaly",
        entity_id=row.id,
        old={"status": old_status},
        new={
            "status": row.status,
            "severity": row.severity,
            "detector": row.detector,
        },
    )
    db.commit()
    db.refresh(row)
    return row


@router.post("/{anomaly_id}/escalate", response_model=AnomalyOut)
def escalate(
    anomaly_id: int,
    payload: EscalationRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin)),
) -> AnomalyDetection:
    """Flag an anomaly for board oversight. Admin-only — independent of the
    status workflow: ops can still ack/resolve, but the board-review flag
    persists until explicitly reviewed via POST /{id}/board-review."""
    row = ensure_anomaly(db, anomaly_id, user.org_id)
    if row.escalation_status == "escalated":
        raise HTTPException(409, "already escalated")

    old = {"escalation_status": row.escalation_status}
    row.escalation_status = "escalated"
    row.escalation_owner = payload.owner
    row.escalation_due_date = payload.due_date
    row.escalation_notes = payload.notes
    row.escalated_at = datetime.utcnow()
    row.board_reviewed_at = None

    write_audit(
        db,
        user=user.email,
        org_id=user.org_id,
        action="escalate",
        entity_type="anomaly",
        entity_id=row.id,
        old=old,
        new={
            "escalation_status": "escalated",
            "owner": payload.owner,
            "due_date": payload.due_date.isoformat() if payload.due_date else None,
            "severity": row.severity,
        },
    )
    db.commit()
    db.refresh(row)
    return row


@router.post("/{anomaly_id}/board-review", response_model=AnomalyOut)
def board_review(
    anomaly_id: int,
    payload: BoardReviewRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin)),
) -> AnomalyDetection:
    """Board member marks an escalated item as reviewed. Admin-only."""
    row = ensure_anomaly(db, anomaly_id, user.org_id)
    if row.escalation_status != "escalated":
        raise HTTPException(409, "anomaly is not escalated")

    row.escalation_status = "board_reviewed"
    row.board_reviewed_at = datetime.utcnow()
    if payload.notes:
        existing = row.escalation_notes or ""
        sep = "\n\n" if existing else ""
        row.escalation_notes = f"{existing}{sep}[board review by {payload.reviewer}]: {payload.notes}"

    write_audit(
        db,
        user=user.email,
        org_id=user.org_id,
        action="board_review",
        entity_type="anomaly",
        entity_id=row.id,
        old={"escalation_status": "escalated"},
        new={
            "escalation_status": "board_reviewed",
            "reviewer": payload.reviewer,
        },
    )
    db.commit()
    db.refresh(row)
    return row
