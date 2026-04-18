from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.api.scoping import ensure_activity, ensure_facility
from app.db.models import ActivityData, Facility, User, UserRole
from app.db.session import get_db
from app.schemas.activity import (
    ActivityCreate,
    ActivityOut,
    ActivityUpdate,
    ActivityWriteResponse,
)
from app.services.audit import write_audit
from app.services.calculation_engine import calculate_for_activity
from app.services.validation import validate_activity

router = APIRouter(prefix="/activities")


def _to_out(a: ActivityData, facility_name: str | None) -> ActivityOut:
    return ActivityOut.model_validate(
        {
            **{k: getattr(a, k) for k in ActivityOut.model_fields if k != "facility_name"},
            "facility_name": facility_name,
        }
    )


@router.get("", response_model=list[ActivityOut])
def list_activities(
    facility_id: int | None = Query(None),
    scope: int | None = Query(None),
    period_start: date | None = Query(None),
    period_end: date | None = Query(None),
    limit: int = Query(200, le=2000),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ActivityOut]:
    stmt = (
        select(ActivityData, Facility.name)
        .join(Facility, ActivityData.facility_id == Facility.id)
        .where(Facility.org_id == user.org_id)
    )
    if facility_id:
        stmt = stmt.where(ActivityData.facility_id == facility_id)
    if scope:
        stmt = stmt.where(ActivityData.scope == scope)
    if period_start:
        stmt = stmt.where(ActivityData.period_start >= period_start)
    if period_end:
        stmt = stmt.where(ActivityData.period_end <= period_end)
    # Newest-inserted first — "recent activity" = most recently added to the ledger,
    # not the most recent emission period. `created_at` ties break by `id`, which is
    # monotonic per insertion so a CSV commit appears as a contiguous block at the top.
    stmt = stmt.order_by(ActivityData.created_at.desc(), ActivityData.id.desc()).limit(limit)
    return [_to_out(row[0], row[1]) for row in db.execute(stmt).all()]


@router.get("/{activity_id}", response_model=ActivityOut)
def get_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ActivityOut:
    activity = ensure_activity(db, activity_id, user.org_id)
    facility = db.get(Facility, activity.facility_id)
    return _to_out(activity, facility.name if facility else None)


@router.post("", response_model=ActivityWriteResponse, status_code=201)
def create_activity(
    payload: ActivityCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin, UserRole.analyst)),
) -> ActivityWriteResponse:
    facility = ensure_facility(db, payload.facility_id, user.org_id)

    result = validate_activity(
        db,
        facility_id=payload.facility_id,
        scope=payload.scope,
        category=payload.category,
        subcategory=payload.subcategory,
        quantity=payload.quantity,
        unit=payload.unit,
        period_start=payload.period_start,
        period_end=payload.period_end,
    )
    if not result.ok:
        raise HTTPException(422, detail=[i.__dict__ for i in result.issues])

    data = payload.model_dump()
    data["uploaded_by"] = user.email
    activity = ActivityData(**data)
    db.add(activity)
    db.flush()

    # Attempt auto-calc in a savepoint so a missing factor doesn't drop the row.
    sp = db.begin_nested()
    try:
        calculate_for_activity(db, activity)
        sp.commit()
    except Exception:
        sp.rollback()

    write_audit(
        db,
        user=user.email,
        action="create",
        entity_type="activity_data",
        entity_id=activity.id,
        new=activity,
        org_id=user.org_id,
    )
    db.commit()
    db.refresh(activity)
    return ActivityWriteResponse(
        activity=_to_out(activity, facility.name),
        validation=[i.__dict__ for i in result.issues],
    )


@router.put("/{activity_id}", response_model=ActivityWriteResponse)
def update_activity(
    activity_id: int,
    payload: ActivityUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin, UserRole.analyst)),
) -> ActivityWriteResponse:
    activity = ensure_activity(db, activity_id, user.org_id)

    updates = payload.model_dump(exclude_unset=True)
    if "facility_id" in updates:
        ensure_facility(db, updates["facility_id"], user.org_id)
    for k, v in updates.items():
        setattr(activity, k, v)

    result = validate_activity(
        db,
        facility_id=activity.facility_id,
        scope=activity.scope,
        category=activity.category,
        subcategory=activity.subcategory,
        quantity=activity.quantity,
        unit=activity.unit,
        period_start=activity.period_start,
        period_end=activity.period_end,
        exclude_id=activity.id,
    )
    if not result.ok:
        db.rollback()
        raise HTTPException(422, detail=[i.__dict__ for i in result.issues])

    db.commit()
    db.refresh(activity)
    facility = db.get(Facility, activity.facility_id)
    return ActivityWriteResponse(
        activity=_to_out(activity, facility.name if facility else None),
        validation=[i.__dict__ for i in result.issues],
    )


@router.delete("/{activity_id}", status_code=204)
def delete_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin)),
) -> None:
    activity = ensure_activity(db, activity_id, user.org_id)
    db.delete(activity)
    db.commit()
