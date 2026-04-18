"""Activity-data validation (Module 5).

Outlier rule: flag a quantity that lies > OUTLIER_SIGMA standard deviations
from the historical mean of the same (facility_id, subcategory, unit) bucket.
We need at least MIN_HISTORY rows to consider history meaningful — anything
less just means "no baseline yet."

Validation never blocks a write. It returns warnings the UI can surface so a
human decides whether the spike is real (e.g., production ramp-up) or a data-
entry error.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ActivityData

OUTLIER_SIGMA = 2.0
MIN_HISTORY = 3


@dataclass
class ValidationIssue:
    severity: str  # "error" | "warning"
    field: str
    message: str


@dataclass
class ValidationResult:
    ok: bool
    issues: list[ValidationIssue]

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "issues": [
                {"severity": i.severity, "field": i.field, "message": i.message}
                for i in self.issues
            ],
        }


def _structural_check(
    *,
    facility_id: int,
    scope: int,
    category: str,
    subcategory: str,
    quantity: float,
    unit: str,
    period_start: date,
    period_end: date,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if scope not in (1, 2, 3):
        issues.append(ValidationIssue("error", "scope", f"scope must be 1, 2, or 3 (got {scope})"))
    if quantity is None or not math.isfinite(quantity) or quantity < 0:
        issues.append(ValidationIssue("error", "quantity", "quantity must be a non-negative number"))
    if not category:
        issues.append(ValidationIssue("error", "category", "category is required"))
    if not subcategory:
        issues.append(ValidationIssue("error", "subcategory", "subcategory is required"))
    if not unit:
        issues.append(ValidationIssue("error", "unit", "unit is required"))
    if not facility_id:
        issues.append(ValidationIssue("error", "facility_id", "facility_id is required"))
    if period_start and period_end and period_end < period_start:
        issues.append(
            ValidationIssue("error", "period_end", "period_end is earlier than period_start")
        )
    return issues


def _outlier_check(
    db: Session,
    *,
    facility_id: int,
    subcategory: str,
    unit: str,
    quantity: float,
    exclude_id: int | None = None,
) -> list[ValidationIssue]:
    """Compare against history for the same (facility, subcategory, unit)."""
    stmt = select(ActivityData.quantity).where(
        ActivityData.facility_id == facility_id,
        ActivityData.subcategory == subcategory,
        ActivityData.unit == unit,
    )
    if exclude_id:
        stmt = stmt.where(ActivityData.id != exclude_id)

    history = [float(q) for q in db.scalars(stmt).all() if q is not None]
    if len(history) < MIN_HISTORY:
        return []

    mean = sum(history) / len(history)
    variance = sum((x - mean) ** 2 for x in history) / len(history)
    std = math.sqrt(variance)
    if std == 0:
        # All historical values identical — flag any deviation.
        if quantity != mean:
            return [
                ValidationIssue(
                    "warning",
                    "quantity",
                    f"quantity {quantity} differs from constant historical value {mean}",
                )
            ]
        return []

    z = (quantity - mean) / std
    if abs(z) > OUTLIER_SIGMA:
        direction = "above" if z > 0 else "below"
        return [
            ValidationIssue(
                "warning",
                "quantity",
                f"quantity {quantity:g} is {abs(z):.1f}σ {direction} historical "
                f"mean {mean:.1f} (n={len(history)}, σ={std:.1f})",
            )
        ]
    return []


def validate_activity(
    db: Session,
    *,
    facility_id: int,
    scope: int,
    category: str,
    subcategory: str,
    quantity: float,
    unit: str,
    period_start: date,
    period_end: date,
    exclude_id: int | None = None,
) -> ValidationResult:
    issues = _structural_check(
        facility_id=facility_id,
        scope=scope,
        category=category,
        subcategory=subcategory,
        quantity=quantity,
        unit=unit,
        period_start=period_start,
        period_end=period_end,
    )

    if not any(i.severity == "error" for i in issues):
        issues.extend(
            _outlier_check(
                db,
                facility_id=facility_id,
                subcategory=subcategory,
                unit=unit,
                quantity=quantity,
                exclude_id=exclude_id,
            )
        )

    ok = not any(i.severity == "error" for i in issues)
    return ValidationResult(ok=ok, issues=issues)
