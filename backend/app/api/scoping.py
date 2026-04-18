"""Helpers for asserting ownership of per-org resources.

Every write endpoint that takes an id in the payload (facility_id, activity_id,
supplier_id, etc.) calls the matching `ensure_*` helper before touching the row
so we never leak or mutate another org's data.
"""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import (
    ActivityData,
    AnomalyDetection,
    Emission,
    Facility,
    Report,
    Scenario,
    Supplier,
    SupplierSubmission,
)


def _forbid(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def ensure_facility(db: Session, facility_id: int, org_id: int) -> Facility:
    f = db.get(Facility, facility_id)
    if f is None or f.org_id != org_id:
        raise _forbid(f"facility {facility_id} not found")
    return f


def ensure_activity(db: Session, activity_id: int, org_id: int) -> ActivityData:
    row = db.get(ActivityData, activity_id)
    if row is None:
        raise _forbid(f"activity {activity_id} not found")
    facility = db.get(Facility, row.facility_id)
    if facility is None or facility.org_id != org_id:
        raise _forbid(f"activity {activity_id} not found")
    return row


def ensure_emission(db: Session, emission_id: int, org_id: int) -> Emission:
    row = db.get(Emission, emission_id)
    if row is None:
        raise _forbid(f"emission {emission_id} not found")
    activity = db.get(ActivityData, row.activity_data_id)
    if activity is None:
        raise _forbid(f"emission {emission_id} not found")
    facility = db.get(Facility, activity.facility_id)
    if facility is None or facility.org_id != org_id:
        raise _forbid(f"emission {emission_id} not found")
    return row


def ensure_supplier(db: Session, supplier_id: int, org_id: int) -> Supplier:
    row = db.get(Supplier, supplier_id)
    if row is None or row.org_id != org_id:
        raise _forbid(f"supplier {supplier_id} not found")
    return row


def ensure_submission(
    db: Session, submission_id: int, org_id: int
) -> SupplierSubmission:
    row = db.get(SupplierSubmission, submission_id)
    if row is None:
        raise _forbid(f"submission {submission_id} not found")
    supplier = db.get(Supplier, row.supplier_id)
    if supplier is None or supplier.org_id != org_id:
        raise _forbid(f"submission {submission_id} not found")
    return row


def ensure_scenario(db: Session, scenario_id: int, org_id: int) -> Scenario:
    row = db.get(Scenario, scenario_id)
    if row is None or row.org_id != org_id:
        raise _forbid(f"scenario {scenario_id} not found")
    return row


def ensure_report(db: Session, report_id: int, org_id: int) -> Report:
    row = db.get(Report, report_id)
    if row is None or row.org_id != org_id:
        raise _forbid(f"report {report_id} not found")
    return row


def ensure_anomaly(db: Session, anomaly_id: int, org_id: int) -> AnomalyDetection:
    row = db.get(AnomalyDetection, anomaly_id)
    if row is None or row.org_id != org_id:
        raise _forbid(f"anomaly {anomaly_id} not found")
    return row
