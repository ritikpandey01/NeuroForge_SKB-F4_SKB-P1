"""Supplier portal — registry CRUD, impact matrix, submission workflow."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.api.scoping import ensure_submission, ensure_supplier
from app.db.models import Supplier, SupplierSubmission, User, UserRole
from app.db.session import get_db
from app.services.audit import write_audit
from app.schemas.supplier import (
    ImpactMatrixOut,
    MatrixCell,
    SupplierCreate,
    SupplierOut,
    SupplierUpdate,
)
from app.schemas.supplier_submission import (
    SubmissionCreate,
    SubmissionOut,
    SubmissionStatusUpdate,
)

router = APIRouter(prefix="/suppliers")


# ── Helpers ───────────────────────────────────────────────────────────


def _to_out(supplier: Supplier, submissions_count: int, latest_status: str | None) -> SupplierOut:
    return SupplierOut.model_validate(
        {
            **{k: getattr(supplier, k) for k in SupplierOut.model_fields
               if k not in ("submissions_count", "latest_submission_status")},
            "submissions_count": submissions_count,
            "latest_submission_status": latest_status,
        }
    )


def _bucket_for_spend(spend: float, low_max: float, medium_max: float) -> str:
    if spend <= low_max:
        return "low"
    if spend <= medium_max:
        return "medium"
    return "high"


# ── Registry CRUD ─────────────────────────────────────────────────────


@router.get("", response_model=list[SupplierOut])
def list_suppliers(
    industry: str | None = Query(None),
    tier: int | None = Query(None, ge=1, le=3),
    data_maturity_level: str | None = Query(None),
    search: str | None = Query(None, description="substring match on name"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[SupplierOut]:
    stmt = (
        select(Supplier)
        .where(Supplier.org_id == user.org_id)
        .order_by(Supplier.annual_spend.desc(), Supplier.id)
    )
    if industry:
        stmt = stmt.where(Supplier.industry == industry)
    if tier:
        stmt = stmt.where(Supplier.tier == tier)
    if data_maturity_level:
        stmt = stmt.where(Supplier.data_maturity_level == data_maturity_level)
    if search:
        stmt = stmt.where(Supplier.name.ilike(f"%{search}%"))

    suppliers = list(db.scalars(stmt).all())
    if not suppliers:
        return []

    supplier_ids = [s.id for s in suppliers]
    counts = dict(
        db.execute(
            select(SupplierSubmission.supplier_id, func.count(SupplierSubmission.id))
            .where(SupplierSubmission.supplier_id.in_(supplier_ids))
            .group_by(SupplierSubmission.supplier_id)
        ).all()
    )

    latest_sub = db.execute(
        select(
            SupplierSubmission.supplier_id,
            SupplierSubmission.status,
            SupplierSubmission.submitted_at,
        )
        .where(SupplierSubmission.supplier_id.in_(supplier_ids))
        .order_by(SupplierSubmission.supplier_id, SupplierSubmission.submitted_at.desc())
    ).all()
    latest_by_supplier: dict[int, str] = {}
    for supplier_id, status, _ in latest_sub:
        latest_by_supplier.setdefault(supplier_id, status)

    return [
        _to_out(s, counts.get(s.id, 0), latest_by_supplier.get(s.id))
        for s in suppliers
    ]


@router.get("/impact-matrix", response_model=ImpactMatrixOut)
def impact_matrix(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ImpactMatrixOut:
    """3×3 grid: spend bucket × data maturity. Buckets use tertiles of the
    current supplier spend distribution so the split adapts to real data."""
    suppliers = list(
        db.scalars(
            select(Supplier)
            .where(Supplier.org_id == user.org_id)
            .order_by(Supplier.annual_spend)
        ).all()
    )
    if not suppliers:
        return ImpactMatrixOut(
            spend_thresholds={"low_max": 0.0, "medium_max": 0.0},
            cells=[],
            total_suppliers=0,
            total_spend=0.0,
        )

    spends = sorted(s.annual_spend for s in suppliers)
    n = len(spends)
    low_max = spends[max(0, n // 3 - 1)]
    medium_max = spends[max(0, (2 * n) // 3 - 1)]

    cells: dict[tuple[str, str], MatrixCell] = {}
    for spend_bucket in ("low", "medium", "high"):
        for maturity in ("spend_based", "activity_based", "verified_primary"):
            cells[(spend_bucket, maturity)] = MatrixCell(
                spend_bucket=spend_bucket,
                data_maturity_level=maturity,
                supplier_count=0,
                total_spend=0.0,
                supplier_ids=[],
            )

    for s in suppliers:
        bucket = _bucket_for_spend(s.annual_spend, low_max, medium_max)
        cell = cells[(bucket, s.data_maturity_level)]
        cell.supplier_count += 1
        cell.total_spend = round(cell.total_spend + s.annual_spend, 2)
        cell.supplier_ids.append(s.id)

    return ImpactMatrixOut(
        spend_thresholds={"low_max": low_max, "medium_max": medium_max},
        cells=list(cells.values()),
        total_suppliers=n,
        total_spend=round(sum(spends), 2),
    )


@router.get("/submissions/all", response_model=list[SubmissionOut])
def list_all_submissions(
    status: str | None = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[SubmissionOut]:
    stmt = (
        select(SupplierSubmission, Supplier.name)
        .join(Supplier, SupplierSubmission.supplier_id == Supplier.id)
        .where(Supplier.org_id == user.org_id)
        .order_by(SupplierSubmission.submitted_at.desc())
        .limit(limit)
    )
    if status:
        stmt = stmt.where(SupplierSubmission.status == status)
    return [_submission_out(sub, supplier_name=name) for sub, name in db.execute(stmt).all()]


@router.get("/{supplier_id}", response_model=SupplierOut)
def get_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SupplierOut:
    supplier = ensure_supplier(db, supplier_id, user.org_id)
    count = db.scalar(
        select(func.count(SupplierSubmission.id)).where(
            SupplierSubmission.supplier_id == supplier_id
        )
    ) or 0
    latest = db.scalars(
        select(SupplierSubmission.status)
        .where(SupplierSubmission.supplier_id == supplier_id)
        .order_by(SupplierSubmission.submitted_at.desc())
        .limit(1)
    ).first()
    return _to_out(supplier, count, latest)


@router.post("", response_model=SupplierOut, status_code=201)
def create_supplier(
    payload: SupplierCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin, UserRole.analyst)),
) -> SupplierOut:
    supplier = Supplier(org_id=user.org_id, **payload.model_dump())
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return _to_out(supplier, 0, None)


@router.put("/{supplier_id}", response_model=SupplierOut)
def update_supplier(
    supplier_id: int,
    payload: SupplierUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin, UserRole.analyst)),
) -> SupplierOut:
    supplier = ensure_supplier(db, supplier_id, user.org_id)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(supplier, k, v)
    db.commit()
    db.refresh(supplier)
    count = db.scalar(
        select(func.count(SupplierSubmission.id)).where(
            SupplierSubmission.supplier_id == supplier_id
        )
    ) or 0
    latest = db.scalars(
        select(SupplierSubmission.status)
        .where(SupplierSubmission.supplier_id == supplier_id)
        .order_by(SupplierSubmission.submitted_at.desc())
        .limit(1)
    ).first()
    return _to_out(supplier, count, latest)


@router.delete("/{supplier_id}", status_code=204)
def delete_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin)),
) -> None:
    supplier = ensure_supplier(db, supplier_id, user.org_id)
    db.delete(supplier)
    db.commit()


# ── Submissions workflow ──────────────────────────────────────────────


@router.get("/{supplier_id}/submissions", response_model=list[SubmissionOut])
def list_submissions(
    supplier_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[SubmissionOut]:
    ensure_supplier(db, supplier_id, user.org_id)
    rows = list(
        db.scalars(
            select(SupplierSubmission)
            .where(SupplierSubmission.supplier_id == supplier_id)
            .order_by(SupplierSubmission.submitted_at.desc())
        ).all()
    )
    return [_submission_out(r) for r in rows]


@router.post(
    "/{supplier_id}/submissions", response_model=SubmissionOut, status_code=201
)
def create_submission(
    supplier_id: int,
    payload: SubmissionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin, UserRole.analyst)),
) -> SubmissionOut:
    supplier = ensure_supplier(db, supplier_id, user.org_id)
    sub = SupplierSubmission(
        supplier_id=supplier_id,
        **payload.model_dump(),
        status="pending",
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return _submission_out(sub, supplier_name=supplier.name)


@router.patch("/submissions/{submission_id}", response_model=SubmissionOut)
def update_submission_status(
    submission_id: int,
    payload: SubmissionStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin, UserRole.analyst)),
) -> SubmissionOut:
    sub = ensure_submission(db, submission_id, user.org_id)
    old_status = sub.status
    sub.status = payload.status
    sub.reviewed_at = datetime.utcnow()
    write_audit(
        db,
        user=user.email,
        org_id=user.org_id,
        action="review",
        entity_type="supplier_submission",
        entity_id=sub.id,
        old={"status": old_status, "reviewed_at": None},
        new={
            "status": sub.status,
            "reviewed_at": sub.reviewed_at.isoformat(),
            "data_quality_score": sub.data_quality_score,
        },
    )
    db.commit()
    db.refresh(sub)
    supplier = db.get(Supplier, sub.supplier_id)
    return _submission_out(sub, supplier_name=supplier.name if supplier else None)


def _submission_out(
    sub: SupplierSubmission, supplier_name: str | None = None
) -> SubmissionOut:
    return SubmissionOut.model_validate(
        {
            **{k: getattr(sub, k) for k in SubmissionOut.model_fields
               if k != "supplier_name"},
            "supplier_name": supplier_name,
        }
    )
