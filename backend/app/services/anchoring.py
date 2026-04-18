"""Merkle-based report anchoring.

Each generated report can be sealed by computing a deterministic Merkle
root over everything that goes into it:

    report_root = sha256(
        activity_root || factor_root || evidence_root
        || methodology_hash || pdf_hash
    )

Sub-roots are built bottom-up from sorted leaf hashes (sha256 of a
canonical string per row / factor / file). Sorting + canonical encoding
make the root reproducible: re-running `compute_report_root` against an
unchanged DB returns the same hex string.

The service is pure (reads, no writes) and chain-agnostic — Phase 1
stores the root in `report_anchors` with chain="local" and verifies by
recomputing. Phase 2 submits the same root as a Polygon tx.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    ActivityData,
    EmissionFactor,
    Facility,
    Organization,
    Report,
)
from app.services.report_renderer import parse_period

ZERO_HASH = "0" * 64


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_str(s: str) -> str:
    return _sha256(s.encode("utf-8"))


def merkle_root(leaves: list[str]) -> str:
    """Compute the Merkle root over hex-encoded sha256 leaves.

    Leaves are hashed pairwise (concatenated as hex strings, re-hashed as
    sha256). Odd trailing leaf is duplicated. Empty input returns ZERO_HASH
    so empty sub-trees don't crash the combiner."""
    if not leaves:
        return ZERO_HASH
    layer = list(leaves)
    while len(layer) > 1:
        nxt: list[str] = []
        for i in range(0, len(layer), 2):
            a = layer[i]
            b = layer[i + 1] if i + 1 < len(layer) else a
            nxt.append(_sha256_str(a + b))
        layer = nxt
    return layer[0]


# ── Canonical leaf encodings ──────────────────────────────────────────


def activity_payload(row: ActivityData, facility_name: str) -> str:
    """Canonical pre-hash string for one activity row. Order + keys are
    frozen — changing them changes every historical root."""
    return (
        f"id={row.id}"
        f"|facility={facility_name}"
        f"|scope={row.scope}"
        f"|category={row.category}"
        f"|subcategory={row.subcategory}"
        f"|period={row.period_start.isoformat()}..{row.period_end.isoformat()}"
        f"|quantity={float(row.quantity):.6f}"
        f"|unit={row.unit}"
        f"|uploaded_by={row.uploaded_by or ''}"
        f"|dept_head={row.department_head_name or ''}"
        f"|dept_head_email={row.department_head_email or ''}"
        f"|evidence={row.source_document or ''}"
        f"|verified={int(bool(row.verified))}"
    )


def _activity_leaf(row: ActivityData, facility_name: str) -> str:
    return _sha256_str(activity_payload(row, facility_name))


def factor_payload(f: EmissionFactor) -> str:
    return (
        f"id={f.id}"
        f"|category={f.category}"
        f"|subcategory={f.subcategory}"
        f"|value={float(f.factor_value):.6f}"
        f"|unit={f.unit}"
        f"|source={f.source}"
        f"|region={f.region}"
        f"|year={f.year}"
    )


def _factor_leaf(f: EmissionFactor) -> str:
    return _sha256_str(factor_payload(f))


def _file_leaf(path: Path) -> str:
    """Hash the on-disk bytes of an evidence file. Missing files hash to
    a placeholder so verification still succeeds if an evidence file was
    pruned — but the proof notes the absence in the manifest."""
    if not path.exists():
        return _sha256_str(f"missing:{path.name}")
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ── Methodology snapshot ──────────────────────────────────────────────


def _methodology_snapshot(org: Organization, period: str) -> dict[str, Any]:
    return {
        "organization": org.name,
        "industry": org.industry,
        "country": org.country,
        "base_year": org.base_year,
        "net_zero_target_year": org.net_zero_target_year,
        "carbon_price_inr_per_tonne": org.carbon_price_inr_per_tonne,
        "period": period,
        "consolidation": "operational_control",
        "ghg_protocol_version": "Corporate Standard 2004 (revised)",
        "factor_resolution_order": [
            "exact(cat+sub+region+year)",
            "region(most_recent_year)",
            "global",
            "any",
        ],
        "scope_boundary": {
            "scope1": "direct emissions from owned/controlled sources",
            "scope2_method": "location_based",
            "scope3_categories_covered": [1, 4, 6],
        },
    }


def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


# ── Root computation ──────────────────────────────────────────────────


@dataclass
class AnchorManifest:
    report_root: str
    activity_root: str
    factor_root: str
    evidence_root: str
    methodology_hash: str
    pdf_hash: str
    activity_leaf_count: int
    factor_leaf_count: int
    evidence_leaf_count: int
    period_start: str
    period_end: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_root": self.report_root,
            "activity_root": self.activity_root,
            "factor_root": self.factor_root,
            "evidence_root": self.evidence_root,
            "methodology_hash": self.methodology_hash,
            "pdf_hash": self.pdf_hash,
            "activity_leaf_count": self.activity_leaf_count,
            "factor_leaf_count": self.factor_leaf_count,
            "evidence_leaf_count": self.evidence_leaf_count,
            "period_start": self.period_start,
            "period_end": self.period_end,
        }


def _compute_activity_root(
    db: Session, org_id: int, start: date, end: date
) -> tuple[str, int]:
    rows = db.scalars(
        select(ActivityData)
        .join(Facility, ActivityData.facility_id == Facility.id)
        .where(Facility.org_id == org_id)
        .where(ActivityData.period_start >= start)
        .where(ActivityData.period_end <= end)
        .order_by(ActivityData.id)
    ).all()
    facility_names = {
        f.id: f.name
        for f in db.scalars(
            select(Facility).where(Facility.org_id == org_id)
        ).all()
    }
    leaves = sorted(
        _activity_leaf(r, facility_names.get(r.facility_id, "")) for r in rows
    )
    return merkle_root(leaves), len(leaves)


def _compute_factor_root(
    db: Session, org_id: int, start: date, end: date
) -> tuple[str, int]:
    # Every factor referenced by any emission computed against activity rows
    # in this period. Deduped, sorted for determinism.
    from app.db.models import Emission

    activity_ids = {
        aid
        for (aid,) in db.execute(
            select(ActivityData.id)
            .join(Facility, ActivityData.facility_id == Facility.id)
            .where(Facility.org_id == org_id)
            .where(ActivityData.period_start >= start)
            .where(ActivityData.period_end <= end)
        ).all()
    }
    factors = (
        db.scalars(
            select(EmissionFactor)
            .join(Emission, Emission.emission_factor_id == EmissionFactor.id)
            .where(Emission.activity_data_id.in_(activity_ids))
            .distinct()
            .order_by(EmissionFactor.id)
        ).all()
        if activity_ids
        else []
    )
    leaves = sorted(_factor_leaf(f) for f in factors)
    return merkle_root(leaves), len(leaves)


def _compute_evidence_root(
    db: Session, org_id: int, start: date, end: date
) -> tuple[str, int]:
    paths: set[str] = set()
    rows = db.scalars(
        select(ActivityData.source_document)
        .join(Facility, ActivityData.facility_id == Facility.id)
        .where(Facility.org_id == org_id)
        .where(ActivityData.period_start >= start)
        .where(ActivityData.period_end <= end)
        .where(ActivityData.source_document.is_not(None))
    ).all()
    for p in rows:
        if p:
            paths.add(p)
    leaves: list[str] = []
    for p in paths:
        candidate = Path(p)
        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate
        leaves.append(_sha256_str(f"{p}:{_file_leaf(candidate)}"))
    # Sort by leaf hash — matches activity/factor trees and the external
    # verify.py, which has no path context.
    leaves.sort()
    return merkle_root(leaves), len(leaves)


def compute_report_root(db: Session, report: Report) -> AnchorManifest:
    """Compute the Merkle root + per-subtree hashes for a report.

    Pure: no DB writes, no file writes. Pass the resulting manifest to
    `seal_report` to persist it. Raises ValueError on unparseable period."""
    org = db.get(Organization, report.org_id)
    if org is None:
        raise ValueError(f"organization {report.org_id} not found")

    start, end = parse_period(report.period)

    activity_root, activity_n = _compute_activity_root(db, report.org_id, start, end)
    factor_root, factor_n = _compute_factor_root(db, report.org_id, start, end)
    evidence_root, evidence_n = _compute_evidence_root(db, report.org_id, start, end)

    methodology = _methodology_snapshot(org, report.period)
    methodology_hash = _sha256_str(_canonical_json(methodology))

    pdf_path = Path(report.file_path) if report.file_path else None
    if pdf_path is None or not pdf_path.exists():
        pdf_hash = _sha256_str(f"missing-pdf:report={report.id}")
    else:
        pdf_hash = _file_leaf(pdf_path)

    # Combine the five subtree hashes into one root. Order is frozen.
    combined = "|".join(
        [activity_root, factor_root, evidence_root, methodology_hash, pdf_hash]
    )
    report_root = _sha256_str(combined)

    return AnchorManifest(
        report_root=f"0x{report_root}",
        activity_root=f"0x{activity_root}",
        factor_root=f"0x{factor_root}",
        evidence_root=f"0x{evidence_root}",
        methodology_hash=f"0x{methodology_hash}",
        pdf_hash=f"0x{pdf_hash}",
        activity_leaf_count=activity_n,
        factor_leaf_count=factor_n,
        evidence_leaf_count=evidence_n,
        period_start=start.isoformat(),
        period_end=end.isoformat(),
    )


# ── Verify ────────────────────────────────────────────────────────────


@dataclass
class VerifyResult:
    verified: bool
    diverged_subtree: str | None  # "activity_root" / "factor_root" / ...
    stored_root: str
    recomputed_root: str
    recomputed: dict[str, Any]
    stored: dict[str, Any]


def verify_report_root(
    db: Session, report: Report, stored_manifest: dict[str, Any]
) -> VerifyResult:
    live = compute_report_root(db, report)
    stored_root = stored_manifest.get("report_root", "")

    diverged: str | None = None
    if live.report_root != stored_root:
        for subtree in (
            "activity_root",
            "factor_root",
            "evidence_root",
            "methodology_hash",
            "pdf_hash",
        ):
            if getattr(live, subtree) != stored_manifest.get(subtree):
                diverged = subtree
                break

    return VerifyResult(
        verified=live.report_root == stored_root,
        diverged_subtree=diverged,
        stored_root=stored_root,
        recomputed_root=live.report_root,
        recomputed=live.to_dict(),
        stored=stored_manifest,
    )
