"""Statistical anomaly detection over activity_data + supplier_submissions.

Deliberately stat-only (no ML training) — at 390 activity rows × 3 facilities
you don't have enough data for a learned model that outperforms z-scores, and
interpretability matters ("3.2σ above trailing 12-month mean" is auditable).

Four detectors:
  1. outlier_zscore — per (facility, subcategory, unit), flag quantities > 2σ
     from the trailing mean. Reuses the same logic as services/validation.py
     but runs across the full table instead of on a single insert.
  2. period_gap — per (facility, subcategory) pair that normally reports
     monthly, detect missing months in the last 12.
  3. zero_value — supplier submissions reporting 0 tCO2e. Implausible for any
     active industrial supplier.
  4. spike_pct — period-over-period jumps > 150% that aren't seasonal.

Each detector produces `AnomalyCandidate` dataclasses; `run_scan` then
upserts them into `anomaly_detections` keyed by fingerprint so re-running
doesn't duplicate.

LLM explanation happens in a separate pass (`explain_pending`) so a detection
run is deterministic and instant; LLM latency/cost is contained to the
explanation step which can be deferred or skipped.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from openai import APIError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.llm_client import CircuitBreakerOpen, LLMNotConfigured, llm
from app.db.models import (
    ActivityData,
    AnomalyDetection,
    Facility,
    Supplier,
    SupplierSubmission,
)

OUTLIER_SIGMA = 2.0
MIN_HISTORY = 3
SPIKE_PCT_THRESHOLD = 1.5  # 150% increase = candidate spike
GAP_LOOKBACK_MONTHS = 12


# ── Candidates (pre-persistence) ──────────────────────────────────────


@dataclass
class AnomalyCandidate:
    detector: str
    severity: str
    subject_type: str
    subject_id: int | None
    title: str
    description: str
    fingerprint: str
    facility_id: int | None = None
    supplier_id: int | None = None
    metric_value: float | None = None
    expected_value: float | None = None
    z_score: float | None = None
    context: dict[str, Any] = field(default_factory=dict)


def _fp(*parts: Any) -> str:
    """Deterministic fingerprint for dedupe across scans."""
    joined = "|".join(str(p) for p in parts)
    return hashlib.sha1(joined.encode("utf-8")).hexdigest()[:24]


def _severity_for_z(z: float) -> str:
    z = abs(z)
    if z >= 4:
        return "critical"
    if z >= 3:
        return "high"
    if z >= 2.5:
        return "medium"
    return "low"


# ── Detector 1: z-score outliers on activity quantities ───────────────


def _detect_outliers(db: Session, org_id: int) -> list[AnomalyCandidate]:
    """Group activity rows by (facility, subcategory, unit) and flag any row
    that lies > 2σ from the group mean. Uses the full history as the
    reference distribution (not trailing) — for a 24-month seed this gives
    stable baselines; in production you'd want trailing + seasonal."""
    rows = db.execute(
        select(
            ActivityData.id,
            ActivityData.facility_id,
            ActivityData.subcategory,
            ActivityData.unit,
            ActivityData.quantity,
            ActivityData.period_start,
            Facility.name,
        )
        .join(Facility, ActivityData.facility_id == Facility.id)
        .where(Facility.org_id == org_id)
    ).all()

    groups: dict[tuple[int, str, str], list[tuple[int, float, date, str]]] = defaultdict(list)
    for r in rows:
        groups[(r.facility_id, r.subcategory, r.unit)].append(
            (r.id, float(r.quantity), r.period_start, r.name)
        )

    out: list[AnomalyCandidate] = []
    for (facility_id, subcategory, unit), points in groups.items():
        if len(points) < MIN_HISTORY:
            continue
        qs = [p[1] for p in points]
        mean = sum(qs) / len(qs)
        variance = sum((x - mean) ** 2 for x in qs) / len(qs)
        std = math.sqrt(variance)
        if std == 0:
            continue

        for activity_id, qty, period, fname in points:
            z = (qty - mean) / std
            if abs(z) <= OUTLIER_SIGMA:
                continue
            direction = "above" if z > 0 else "below"
            out.append(
                AnomalyCandidate(
                    detector="outlier_zscore",
                    severity=_severity_for_z(z),
                    subject_type="activity_data",
                    subject_id=activity_id,
                    facility_id=facility_id,
                    title=(
                        f"{fname} · {subcategory} quantity {abs(z):.1f}σ {direction} "
                        f"historical mean ({period:%Y-%m})"
                    ),
                    description=(
                        f"Reported quantity {qty:g} {unit} for {subcategory} at "
                        f"{fname} on {period:%Y-%m}. Historical mean across "
                        f"{len(qs)} periods is {mean:.1f} {unit} (σ={std:.1f})."
                    ),
                    metric_value=qty,
                    expected_value=mean,
                    z_score=z,
                    fingerprint=_fp("outlier", activity_id),
                    context={
                        "facility_name": fname,
                        "subcategory": subcategory,
                        "unit": unit,
                        "period": period.isoformat(),
                        "history_n": len(qs),
                        "history_std": std,
                    },
                )
            )
    return out


# ── Detector 2: missing-period gaps ────────────────────────────────────


def _month_key(d: date) -> str:
    return d.strftime("%Y-%m")


def _expected_month_keys(start: date, end: date) -> list[str]:
    """Inclusive YYYY-MM list from start..end."""
    out: list[str] = []
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            m = 1
            y += 1
    return out


def _detect_period_gaps(db: Session, org_id: int) -> list[AnomalyCandidate]:
    """For each (facility, subcategory) pair that reports regularly (≥6
    months in a 12-month window), flag any months in that window that are
    missing. Designed to catch "Nov–Dec 2024 Mumbai office electricity —
    missing entirely" type anomalies."""
    rows = db.execute(
        select(
            ActivityData.facility_id,
            ActivityData.subcategory,
            ActivityData.period_start,
            Facility.name,
        )
        .join(Facility, ActivityData.facility_id == Facility.id)
        .where(Facility.org_id == org_id)
    ).all()

    by_pair: dict[tuple[int, str], dict[str, date]] = defaultdict(dict)
    names: dict[int, str] = {}
    for r in rows:
        by_pair[(r.facility_id, r.subcategory)][_month_key(r.period_start)] = r.period_start
        names[r.facility_id] = r.name

    out: list[AnomalyCandidate] = []
    for (facility_id, subcategory), months in by_pair.items():
        if len(months) < 6:
            continue
        sorted_keys = sorted(months.keys())
        last_seen = months[sorted_keys[-1]]
        first_seen = months[sorted_keys[0]]
        expected = _expected_month_keys(first_seen, last_seen)
        missing = [k for k in expected if k not in months]
        if not missing:
            continue
        # Skip subcategories that are inherently sporadic (refrigerant recharge,
        # flights, etc.) — if more than 30% of the window is missing, the series
        # isn't monthly in the first place and every gap is a false positive.
        if len(missing) / len(expected) > 0.30:
            continue
        # Collapse contiguous missing months into a single anomaly per run.
        out.append(
            AnomalyCandidate(
                detector="period_gap",
                severity="high" if len(missing) >= 2 else "medium",
                subject_type="facility_gap",
                subject_id=None,
                facility_id=facility_id,
                title=(
                    f"{names[facility_id]} · {subcategory} — {len(missing)} missing "
                    f"period(s): {', '.join(missing)}"
                ),
                description=(
                    f"Reporting for {subcategory} at {names[facility_id]} is continuous "
                    f"from {sorted_keys[0]} to {sorted_keys[-1]} except for "
                    f"{', '.join(missing)}. A gap this size is almost always a "
                    f"data-collection failure rather than zero activity."
                ),
                metric_value=float(len(missing)),
                expected_value=float(len(expected)),
                fingerprint=_fp("gap", facility_id, subcategory, *missing),
                context={
                    "facility_name": names[facility_id],
                    "subcategory": subcategory,
                    "missing_months": missing,
                    "first_seen": sorted_keys[0],
                    "last_seen": sorted_keys[-1],
                },
            )
        )
    return out


# ── Detector 3: zero-value supplier submissions ───────────────────────


def _detect_zero_submissions(db: Session, org_id: int) -> list[AnomalyCandidate]:
    rows = db.execute(
        select(SupplierSubmission, Supplier)
        .join(Supplier, SupplierSubmission.supplier_id == Supplier.id)
        .where(Supplier.org_id == org_id)
    ).all()

    out: list[AnomalyCandidate] = []
    for sub, supplier in rows:
        reported = sub.submitted_data.get("total_emissions_tco2e")
        try:
            value = float(reported) if reported is not None else None
        except (TypeError, ValueError):
            value = None

        if value is None or value > 0:
            continue

        out.append(
            AnomalyCandidate(
                detector="zero_value",
                severity="high",
                subject_type="supplier_submission",
                subject_id=sub.id,
                supplier_id=supplier.id,
                title=(
                    f"{supplier.name} reported 0 tCO₂e for {sub.period} — "
                    f"implausible for active supplier"
                ),
                description=(
                    f"{supplier.name} ({supplier.industry}, {supplier.scope3_category}) "
                    f"submitted a {sub.period} report with total_emissions_tco2e = 0. "
                    f"Annual spend is ₹{supplier.annual_spend} Cr — zero emissions is "
                    f"extremely unlikely to be a true reading and typically indicates "
                    f"missing scope coverage or a methodology error."
                ),
                metric_value=0.0,
                fingerprint=_fp("zero_sub", sub.id),
                context={
                    "supplier_name": supplier.name,
                    "supplier_industry": supplier.industry,
                    "period": sub.period,
                    "annual_spend_cr": supplier.annual_spend,
                    "methodology": sub.submitted_data.get("methodology"),
                },
            )
        )
    return out


# ── Detector 4: period-over-period spikes ────────────────────────────


def _detect_spikes(db: Session, org_id: int) -> list[AnomalyCandidate]:
    """Flag a month whose value is >150% of the prior month for the same
    (facility, subcategory). Complements the z-score detector by catching
    sudden shifts in cases where history is too short for a clean σ."""
    rows = db.execute(
        select(
            ActivityData.id,
            ActivityData.facility_id,
            ActivityData.subcategory,
            ActivityData.unit,
            ActivityData.quantity,
            ActivityData.period_start,
            Facility.name,
        )
        .join(Facility, ActivityData.facility_id == Facility.id)
        .where(Facility.org_id == org_id)
        .order_by(ActivityData.facility_id, ActivityData.subcategory, ActivityData.period_start)
    ).all()

    by_pair: dict[tuple[int, str], list[Any]] = defaultdict(list)
    for r in rows:
        by_pair[(r.facility_id, r.subcategory)].append(r)

    out: list[AnomalyCandidate] = []
    for (_, subcategory), series in by_pair.items():
        for prev, cur in zip(series, series[1:]):
            if prev.quantity <= 0:
                continue
            ratio = cur.quantity / prev.quantity
            if ratio - 1.0 < SPIKE_PCT_THRESHOLD:
                continue
            pct = (ratio - 1.0) * 100
            out.append(
                AnomalyCandidate(
                    detector="spike_pct",
                    severity="high" if ratio >= 3.0 else "medium",
                    subject_type="activity_data",
                    subject_id=cur.id,
                    facility_id=cur.facility_id,
                    title=(
                        f"{cur.name} · {subcategory} jumped {pct:.0f}% month-over-month "
                        f"({cur.period_start:%Y-%m})"
                    ),
                    description=(
                        f"{subcategory} at {cur.name} was {prev.quantity:g} {cur.unit} in "
                        f"{prev.period_start:%Y-%m} and {cur.quantity:g} {cur.unit} in "
                        f"{cur.period_start:%Y-%m} — a {pct:.0f}% increase. Confirm "
                        f"operational cause (commissioning, production ramp) before "
                        f"accepting."
                    ),
                    metric_value=cur.quantity,
                    expected_value=prev.quantity,
                    fingerprint=_fp("spike", cur.id),
                    context={
                        "facility_name": cur.name,
                        "subcategory": subcategory,
                        "prev_period": prev.period_start.isoformat(),
                        "cur_period": cur.period_start.isoformat(),
                        "ratio": ratio,
                    },
                )
            )
    return out


# ── Orchestration ─────────────────────────────────────────────────────


def _upsert(db: Session, cand: AnomalyCandidate, org_id: int) -> AnomalyDetection:
    existing = db.scalar(
        select(AnomalyDetection).where(AnomalyDetection.fingerprint == cand.fingerprint)
    )
    if existing:
        # Refresh the description/severity in case the data around the anomaly
        # changed — but preserve ack state and LLM explanation.
        existing.severity = cand.severity
        existing.title = cand.title
        existing.description = cand.description
        existing.metric_value = cand.metric_value
        existing.expected_value = cand.expected_value
        existing.z_score = cand.z_score
        existing.context = cand.context
        if existing.org_id is None:
            existing.org_id = org_id
        return existing

    row = AnomalyDetection(
        org_id=org_id,
        detector=cand.detector,
        severity=cand.severity,
        subject_type=cand.subject_type,
        subject_id=cand.subject_id,
        facility_id=cand.facility_id,
        supplier_id=cand.supplier_id,
        title=cand.title,
        description=cand.description,
        metric_value=cand.metric_value,
        expected_value=cand.expected_value,
        z_score=cand.z_score,
        fingerprint=cand.fingerprint,
        context=cand.context,
    )
    db.add(row)
    return row


def run_scan(db: Session, org_id: int) -> dict[str, Any]:
    """Run all four detectors scoped to a single org, upsert, commit."""
    cands: list[AnomalyCandidate] = []
    cands.extend(_detect_outliers(db, org_id))
    cands.extend(_detect_period_gaps(db, org_id))
    cands.extend(_detect_zero_submissions(db, org_id))
    cands.extend(_detect_spikes(db, org_id))

    new_count = 0
    updated_count = 0
    for c in cands:
        existing = db.scalar(
            select(AnomalyDetection.id).where(AnomalyDetection.fingerprint == c.fingerprint)
        )
        _upsert(db, c, org_id)
        if existing:
            updated_count += 1
        else:
            new_count += 1

    db.commit()

    by_severity: dict[str, int] = defaultdict(int)
    for c in cands:
        by_severity[c.severity] += 1

    return {
        "total_detected": len(cands),
        "new": new_count,
        "updated": updated_count,
        "by_severity": dict(by_severity),
        "by_detector": {
            d: sum(1 for c in cands if c.detector == d)
            for d in ("outlier_zscore", "period_gap", "zero_value", "spike_pct")
        },
    }


# ── LLM explanation pass ──────────────────────────────────────────────


_SYSTEM_PROMPT = """You are a senior ESG analyst reviewing flagged anomalies in a corporate GHG inventory.

For each anomaly, write a 2–3 sentence plain-English explanation for a non-technical reviewer. Cover:
  1. What specifically is unusual (one sentence, concrete numbers).
  2. The most likely benign explanation AND the most likely problematic explanation.
  3. One next action the reviewer should take.

Be direct. No hedging language. No bullet points. No headings. Just prose."""


def _build_user_prompt(row: AnomalyDetection) -> str:
    ctx = json.dumps(row.context, default=str, ensure_ascii=False)
    return (
        f"Detector: {row.detector}\n"
        f"Severity: {row.severity}\n"
        f"Title: {row.title}\n"
        f"Description: {row.description}\n"
        f"Context: {ctx}"
    )


def explain_pending(db: Session, *, org_id: int, limit: int = 20) -> dict[str, Any]:
    """Generate LLM explanations for any anomaly rows that don't have one yet.
    Fails gracefully — if the key is missing or the circuit is open, the
    detections stay in the table without an explanation (the UI falls back
    to the deterministic description)."""
    rows = list(
        db.scalars(
            select(AnomalyDetection)
            .where(AnomalyDetection.llm_explanation.is_(None))
            .where(AnomalyDetection.org_id == org_id)
            .order_by(AnomalyDetection.detected_at.desc())
            .limit(limit)
        ).all()
    )
    if not rows:
        return {"explained": 0, "skipped_reason": None, "attempted": 0}

    explained = 0
    skipped_reason: str | None = None

    for row in rows:
        try:
            resp = llm.chat_completions_create(
                model=settings.OPENAI_MODEL,
                max_tokens=300,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": _build_user_prompt(row)},
                ],
            )
        except LLMNotConfigured:
            skipped_reason = "OPENAI_API_KEY not set"
            break
        except CircuitBreakerOpen as e:
            skipped_reason = f"circuit open: {e}"
            break
        except APIError as e:
            skipped_reason = f"LLM upstream: {getattr(e, 'message', None) or str(e)}"
            break

        text = (resp.choices[0].message.content or "").strip()
        if text:
            row.llm_explanation = text
            row.llm_explained_at = datetime.utcnow()
            explained += 1

    if explained:
        db.commit()

    return {
        "explained": explained,
        "attempted": len(rows),
        "skipped_reason": skipped_reason,
    }
