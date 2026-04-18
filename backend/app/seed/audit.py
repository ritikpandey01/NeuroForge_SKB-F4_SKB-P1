"""Seed audit log entries that reflect plausible historical activity.

The audit_log table has real value only when it spans many actions over
time. Rather than retro-logging every seeded row (noisy, repetitive),
this generates a representative sample per org:

- activity_data creates + CSV bulk commits
- supplier submission reviews (approve / reject / flag)
- report generations + downloads
- anomaly acknowledge / dismiss / resolve
- facility and supplier edits (occasional)

Entries are deterministic via a seeded RNG so re-running yields the same
trail, and timestamps are spread across the org's activity window.
"""

from __future__ import annotations

import json
import random
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.db.models import (
    ActivityData,
    AnomalyDetection,
    AuditLog,
    Facility,
    Organization,
    Report,
    Supplier,
    SupplierSubmission,
)


# Per-org user roster. The email shape has to match the org's domain or
# the trail reads as synthetic on a glance. The last entry in each list
# is the system actor (batch uploads, anomaly scanner).
_ROSTERS: dict[str, dict[str, list[str]]] = {
    "greenfield": {
        "users": [
            "esg.lead@greenfieldmfg.in",
            "ops.manager@greenfieldmfg.in",
            "facility.admin.pune@greenfieldmfg.in",
            "facility.admin.chennai@greenfieldmfg.in",
            "auditor.external@kpmg-india.com",
        ],
        "esg_lead": "esg.lead@greenfieldmfg.in",
        "auditor": "auditor.external@kpmg-india.com",
        "facility_admins": [
            "facility.admin.pune@greenfieldmfg.in",
            "facility.admin.chennai@greenfieldmfg.in",
        ],
        "seed": 20260418,
    },
    "ultratech": {
        "users": [
            "sustainability.head@ultratechcement.com",
            "plant.ops.rawan@ultratechcement.com",
            "plant.ops.awarpur@ultratechcement.com",
            "plant.ops.kovaya@ultratechcement.com",
            "carbon.analyst@ultratechcement.com",
            "auditor.external@deloitte.co.in",
        ],
        "esg_lead": "sustainability.head@ultratechcement.com",
        "auditor": "auditor.external@deloitte.co.in",
        "facility_admins": [
            "plant.ops.rawan@ultratechcement.com",
            "plant.ops.awarpur@ultratechcement.com",
            "plant.ops.kovaya@ultratechcement.com",
        ],
        "seed": 20260419,
    },
}

SYSTEM_USER = "system@carbonlens.local"


def _rand_user(rng: random.Random, roster: list[str], weight_system: float = 0.15) -> str:
    if rng.random() < weight_system:
        return SYSTEM_USER
    return rng.choice(roster)


def _ts(rng: random.Random, base: datetime, jitter_days: int) -> datetime:
    offset = timedelta(
        days=rng.uniform(0, jitter_days),
        hours=rng.uniform(0, 23),
        minutes=rng.uniform(0, 59),
    )
    return base + offset


def _activity_new(row: ActivityData) -> str:
    return json.dumps(
        {
            "facility_id": row.facility_id,
            "scope": row.scope,
            "category": row.category,
            "subcategory": row.subcategory,
            "quantity": float(row.quantity),
            "unit": row.unit,
            "period_start": row.period_start.isoformat(),
            "period_end": row.period_end.isoformat(),
            "verified": row.verified,
        },
        sort_keys=True,
    )


def _submission_review_diff(
    sub: SupplierSubmission, old_status: str
) -> tuple[str, str]:
    old = json.dumps(
        {
            "status": old_status,
            "reviewed_at": None,
            "data_quality_score": sub.data_quality_score,
        },
        sort_keys=True,
    )
    new = json.dumps(
        {
            "status": sub.status,
            "reviewed_at": (
                sub.reviewed_at.isoformat() if sub.reviewed_at else None
            ),
            "data_quality_score": sub.data_quality_score,
        },
        sort_keys=True,
    )
    return old, new


def _anomaly_transition(anom: AnomalyDetection, old_status: str) -> tuple[str, str]:
    old = json.dumps({"status": old_status}, sort_keys=True)
    new = json.dumps(
        {
            "status": anom.status,
            "severity": anom.severity,
            "detector": anom.detector,
        },
        sort_keys=True,
    )
    return old, new


def _seed_org(db: Session, org: Organization, roster: dict) -> int:
    rng = random.Random(roster["seed"])
    users = roster["users"]
    esg_lead = roster["esg_lead"]
    auditor = roster["auditor"]
    facility_admins = roster["facility_admins"]

    fac_ids = [
        fid for (fid,) in db.query(Facility.id).filter_by(org_id=org.id).all()
    ]
    activities = (
        db.query(ActivityData)
        .filter(ActivityData.facility_id.in_(fac_ids))
        .order_by(ActivityData.id)
        .all()
    )
    if not activities:
        print(f"  no activity data for {org.name} — skipping audit seed")
        return 0

    suppliers = db.query(Supplier).filter_by(org_id=org.id).all()
    supplier_ids = [s.id for s in suppliers]
    submissions = (
        db.query(SupplierSubmission)
        .filter(SupplierSubmission.supplier_id.in_(supplier_ids))
        .all()
        if supplier_ids
        else []
    )
    reports = db.query(Report).filter_by(org_id=org.id).all()
    anomalies = db.query(AnomalyDetection).filter_by(org_id=org.id).all()

    entries: list[AuditLog] = []

    sample_size = min(60, len(activities)) if org.id != 1 else min(50, len(activities))
    sampled_activities = rng.sample(activities, sample_size)
    for row in sampled_activities:
        base = datetime.combine(row.period_end, datetime.min.time())
        ts = _ts(rng, base, jitter_days=5)
        entries.append(
            AuditLog(
                org_id=org.id,
                user=_rand_user(rng, users, weight_system=0.25),
                action="create",
                entity_type="activity_data",
                entity_id=row.id,
                old_value=None,
                new_value=_activity_new(row),
                timestamp=ts,
            )
        )

    for row in rng.sample(activities, min(10, len(activities))):
        base = datetime.combine(row.period_end, datetime.min.time()) + timedelta(days=10)
        ts = _ts(rng, base, jitter_days=7)
        old = json.dumps(
            {"verified": False, "quantity": float(row.quantity) * 1.05},
            sort_keys=True,
        )
        new = json.dumps(
            {"verified": True, "quantity": float(row.quantity)}, sort_keys=True
        )
        entries.append(
            AuditLog(
                org_id=org.id,
                user=_rand_user(rng, users),
                action="update",
                entity_type="activity_data",
                entity_id=row.id,
                old_value=old,
                new_value=new,
                timestamp=ts,
            )
        )

    status_predecessor = {
        "accepted": "pending",
        "rejected": "pending",
        "flagged": "pending",
    }
    for sub in submissions:
        if sub.reviewed_at is None:
            continue
        old_status = status_predecessor.get(sub.status, "pending")
        old, new = _submission_review_diff(sub, old_status)
        entries.append(
            AuditLog(
                org_id=org.id,
                user=rng.choice([esg_lead, auditor]),
                action="review",
                entity_type="supplier_submission",
                entity_id=sub.id,
                old_value=old,
                new_value=new,
                timestamp=sub.reviewed_at,
            )
        )

    for sup in rng.sample(suppliers, min(4, len(suppliers))):
        base = datetime.utcnow() - timedelta(days=rng.randint(30, 300))
        old = json.dumps({"data_maturity_level": "spend_based"}, sort_keys=True)
        new = json.dumps(
            {"data_maturity_level": sup.data_maturity_level}, sort_keys=True
        )
        entries.append(
            AuditLog(
                org_id=org.id,
                user=esg_lead,
                action="update",
                entity_type="supplier",
                entity_id=sup.id,
                old_value=old,
                new_value=new,
                timestamp=base,
            )
        )

    for rep in reports:
        entries.append(
            AuditLog(
                org_id=org.id,
                user=esg_lead,
                action="generate",
                entity_type="report",
                entity_id=rep.id,
                old_value=None,
                new_value=json.dumps(
                    {
                        "report_type": rep.report_type,
                        "period": rep.period,
                        "status": rep.status,
                    },
                    sort_keys=True,
                ),
                timestamp=rep.generated_at,
            )
        )

    for anom in rng.sample(anomalies, min(12, len(anomalies))):
        old_status = "new"
        new_status = rng.choice(["acknowledged", "dismissed", "resolved"])
        stub = AnomalyDetection(
            status=new_status,
            severity=anom.severity,
            detector=anom.detector,
        )
        old, new = _anomaly_transition(stub, old_status)
        base = anom.detected_at + timedelta(days=rng.randint(1, 10))
        entries.append(
            AuditLog(
                org_id=org.id,
                user=_rand_user(rng, users),
                action=new_status if new_status != "acknowledged" else "acknowledge",
                entity_type="anomaly",
                entity_id=anom.id,
                old_value=old,
                new_value=new,
                timestamp=base,
            )
        )

    batches = 6 if org.id != 1 else 4
    for _ in range(batches):
        batch_size = rng.randint(12, 28)
        base = datetime.utcnow() - timedelta(days=rng.randint(15, 400))
        entries.append(
            AuditLog(
                org_id=org.id,
                user=SYSTEM_USER,
                action="bulk_create",
                entity_type="activity_data",
                entity_id=0,
                old_value=None,
                new_value=json.dumps(
                    {
                        "rows_inserted": batch_size,
                        "source": "csv_upload",
                        "submitted_by": rng.choice(facility_admins),
                    },
                    sort_keys=True,
                ),
                timestamp=base,
            )
        )

    entries.sort(key=lambda e: e.timestamp)
    db.add_all(entries)
    db.flush()
    print(f"  inserted {len(entries)} audit log entries for {org.name}")
    return len(entries)


def seed(db: Session) -> None:
    # Per-org short-circuit — rerunning won't duplicate but will fill in
    # orgs that were previously skipped.
    for org in db.query(Organization).all():
        if db.query(AuditLog).filter_by(org_id=org.id).count() > 0:
            continue
        key = (
            "greenfield" if "Greenfield" in org.name
            else "ultratech" if "UltraTech" in org.name
            else None
        )
        if key is None:
            continue
        _seed_org(db, org, _ROSTERS[key])
