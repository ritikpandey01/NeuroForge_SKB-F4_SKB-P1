"""Seed 2 pre-escalated anomalies so the Board Review queue is non-empty
on first load.

Picks the 2 highest-severity existing anomalies and marks them escalated
with different owners / due dates. Idempotent: only runs if no anomalies
are currently escalated.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AnomalyDetection


def seed(db: Session) -> None:
    existing = db.scalar(
        select(AnomalyDetection).where(
            AnomalyDetection.escalation_status.is_not(None)
        )
    )
    if existing is not None:
        print("  escalations already present, skipping")
        return

    severity_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    all_anoms = list(db.scalars(select(AnomalyDetection)).all())
    if not all_anoms:
        print("  no anomalies to escalate, skipping")
        return

    all_anoms.sort(
        key=lambda r: (severity_rank.get(r.severity, 99), -r.detected_at.timestamp())
    )
    top = all_anoms[:2]

    owners_cycle = [
        ("esg.lead@greenfieldmfg.in", 14, "Escalated for board review — material impact on SBTi trajectory"),
        ("cso@greenfieldmfg.in", 7, "Critical deviation; recommend approving remediation budget"),
    ]

    now = datetime.utcnow()
    for anom, (owner, days_out, note) in zip(top, owners_cycle):
        anom.escalation_status = "escalated"
        anom.escalation_owner = owner
        anom.escalation_due_date = date.today() + timedelta(days=days_out)
        anom.escalation_notes = note
        anom.escalated_at = now - timedelta(days=2)

    db.flush()
    print(f"  escalated {len(top)} anomalies for board review")
