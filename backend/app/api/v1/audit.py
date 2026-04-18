"""Audit log read API.

GET /audit-log                — filtered, paginated table
GET /audit-log/filter-options — distinct values to drive filter dropdowns

Writes happen inline at call sites via app.services.audit.write_audit —
see activities, suppliers, anomalies endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import AuditLog, User
from app.db.session import get_db
from app.schemas.audit import AuditEntry, AuditFilterOptions, AuditPage

router = APIRouter(prefix="/audit-log")


@router.get("/filter-options", response_model=AuditFilterOptions)
def filter_options(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AuditFilterOptions:
    entity_types = sorted(
        v
        for (v,) in db.execute(
            select(AuditLog.entity_type).where(AuditLog.org_id == user.org_id).distinct()
        ).all()
        if v
    )
    actions = sorted(
        v
        for (v,) in db.execute(
            select(AuditLog.action).where(AuditLog.org_id == user.org_id).distinct()
        ).all()
        if v
    )
    users = sorted(
        v
        for (v,) in db.execute(
            select(AuditLog.user).where(AuditLog.org_id == user.org_id).distinct()
        ).all()
        if v
    )
    return AuditFilterOptions(
        entity_types=entity_types, actions=actions, users=users
    )


@router.get("", response_model=AuditPage)
def list_audit(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    entity_type: str | None = None,
    action: str | None = None,
    actor: str | None = Query(None, alias="user"),
    date_from: datetime | None = Query(None, alias="from"),
    date_to: datetime | None = Query(None, alias="to"),
    q: str | None = Query(None, description="free-text search in old/new value JSON"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    sort: Literal["desc", "asc"] = "desc",
) -> AuditPage:
    stmt = select(AuditLog).where(AuditLog.org_id == user.org_id)
    count_stmt = select(func.count(AuditLog.id)).where(AuditLog.org_id == user.org_id)

    def _apply_filters(s):
        if entity_type:
            s = s.where(AuditLog.entity_type == entity_type)
        if action:
            s = s.where(AuditLog.action == action)
        if actor:
            s = s.where(AuditLog.user == actor)
        if date_from:
            s = s.where(AuditLog.timestamp >= date_from)
        if date_to:
            s = s.where(AuditLog.timestamp <= date_to)
        if q:
            like = f"%{q}%"
            s = s.where(
                or_(
                    AuditLog.old_value.like(like),
                    AuditLog.new_value.like(like),
                    AuditLog.entity_type.like(like),
                    AuditLog.user.like(like),
                )
            )
        return s

    stmt = _apply_filters(stmt)
    count_stmt = _apply_filters(count_stmt)

    total = db.scalar(count_stmt) or 0

    order_col = AuditLog.timestamp.desc() if sort == "desc" else AuditLog.timestamp.asc()
    rows = list(
        db.scalars(stmt.order_by(order_col, AuditLog.id.desc()).limit(limit).offset(offset)).all()
    )

    return AuditPage(
        total=total,
        limit=limit,
        offset=offset,
        entries=[AuditEntry.model_validate(r) for r in rows],
    )
