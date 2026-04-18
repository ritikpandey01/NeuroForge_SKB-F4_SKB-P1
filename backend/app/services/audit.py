"""Audit trail helper — explicit, call-site writes only.

Usage:
    from app.services.audit import write_audit
    write_audit(db, user="ops.manager@example.com", action="create",
                entity_type="activity_data", entity_id=row.id, new=row)

No middleware, no SQLAlchemy event listeners — we want every audit write
to be visible at the call site so it's obvious what does (and doesn't)
get logged.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AuditLog, Organization

DEFAULT_USER = "system@carbonlens.local"


def _serialize(val: Any) -> str | None:
    if val is None:
        return None
    if isinstance(val, str):
        return val
    if isinstance(val, dict | list):
        return json.dumps(val, default=str, sort_keys=True)
    # SQLAlchemy model: grab column attrs.
    if hasattr(val, "__table__"):
        payload = {c.name: getattr(val, c.name) for c in val.__table__.columns}
        return json.dumps(payload, default=str, sort_keys=True)
    return json.dumps(val, default=str)


def write_audit(
    db: Session,
    *,
    user: str = DEFAULT_USER,
    action: str,
    entity_type: str,
    entity_id: int,
    old: Any = None,
    new: Any = None,
    org_id: int | None = None,
    commit: bool = False,
) -> AuditLog:
    """Append one audit row. Caller controls flush/commit timing.

    `old`/`new` can be dicts, strings, or ORM instances — serialized to JSON.
    `commit=True` is only for standalone writes (seeds, bulk scripts); inside
    request handlers the surrounding transaction should commit.
    """
    if org_id is None:
        org = db.scalars(select(Organization).order_by(Organization.id).limit(1)).first()
        if not org:
            raise RuntimeError("no organization present — cannot write audit log")
        org_id = org.id

    entry = AuditLog(
        org_id=org_id,
        user=user,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=_serialize(old),
        new_value=_serialize(new),
    )
    db.add(entry)
    if commit:
        db.commit()
        db.refresh(entry)
    else:
        db.flush()
    return entry
