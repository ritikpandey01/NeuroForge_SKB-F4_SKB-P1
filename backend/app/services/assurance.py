"""Assurance bundle builder.

Given a sealed report, emit a zip an external auditor can use to
independently reproduce the Merkle root — without trusting our backend,
our database, or our CLI. The bundle is the proof artifact.

Contents:
    manifest.json            per-subtree roots + leaf counts + seal metadata
    methodology.json         pre-hash methodology snapshot
    leaves/activity.jsonl    one line per activity row: canonical payload + leaf hash
    leaves/factors.jsonl     one line per emission factor
    leaves/evidence.jsonl    one line per evidence file: path + file_hash + leaf_hash
    report.pdf               the sealed PDF (hash must match manifest.pdf_hash)
    assurance_certificate.pdf stamped certificate with root + chain info
    verify.py                standalone (stdlib-only) recomputer
    README.md                how to run verify.py

Design choices:
- We do NOT mutate the original PDF. The stored PDF is what was sealed;
  mutating it would invalidate `pdf_hash`. The certificate is a separate
  file.
- verify.py takes no dependencies outside Python stdlib so the auditor
  doesn't need to install anything.
"""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    ActivityData,
    Emission,
    EmissionFactor,
    Facility,
    Organization,
    Report,
    ReportAnchor,
)
from app.services.anchoring import (
    _methodology_snapshot,
    activity_payload,
    factor_payload,
)
from app.services.report_renderer import parse_period


def _sha256_str(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _activity_lines(db: Session, org_id: int, start, end) -> list[dict[str, Any]]:
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
    out: list[dict[str, Any]] = []
    for r in rows:
        payload = activity_payload(r, facility_names.get(r.facility_id, ""))
        out.append({"payload": payload, "leaf": _sha256_str(payload)})
    out.sort(key=lambda x: x["leaf"])
    return out


def _factor_lines(db: Session, org_id: int, start, end) -> list[dict[str, Any]]:
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
    if not activity_ids:
        return []
    factors = db.scalars(
        select(EmissionFactor)
        .join(Emission, Emission.emission_factor_id == EmissionFactor.id)
        .where(Emission.activity_data_id.in_(activity_ids))
        .distinct()
        .order_by(EmissionFactor.id)
    ).all()
    out = [
        {"payload": factor_payload(f), "leaf": _sha256_str(factor_payload(f))}
        for f in factors
    ]
    out.sort(key=lambda x: x["leaf"])
    return out


def _evidence_lines(db: Session, org_id: int, start, end) -> list[dict[str, Any]]:
    paths = {
        p
        for (p,) in db.execute(
            select(ActivityData.source_document)
            .join(Facility, ActivityData.facility_id == Facility.id)
            .where(Facility.org_id == org_id)
            .where(ActivityData.period_start >= start)
            .where(ActivityData.period_end <= end)
            .where(ActivityData.source_document.is_not(None))
        ).all()
        if p
    }
    out: list[dict[str, Any]] = []
    for p in sorted(paths):
        candidate = Path(p)
        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate
        if candidate.exists():
            file_hash = _file_sha256(candidate)
        else:
            file_hash = _sha256_str(f"missing:{candidate.name}")
        payload = f"{p}:{file_hash}"
        out.append(
            {
                "path": p,
                "file_hash": file_hash,
                "leaf": _sha256_str(payload),
                "present": candidate.exists(),
            }
        )
    out.sort(key=lambda x: x["leaf"])
    return out


def _certificate_pdf(
    report: Report,
    org_name: str,
    anchor: ReportAnchor,
    manifest: dict[str, Any],
) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )
    styles = getSampleStyleSheet()
    brand = colors.HexColor("#0F766E")
    slate = colors.HexColor("#0F172A")

    title_style = ParagraphStyle(
        "title",
        parent=styles["Heading1"],
        fontSize=16,
        textColor=brand,
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "subtitle", parent=styles["Normal"], fontSize=10, textColor=slate
    )
    mono_style = ParagraphStyle(
        "mono",
        parent=styles["Normal"],
        fontSize=8,
        fontName="Courier",
        textColor=slate,
        leading=10,
    )

    flow = [
        Paragraph("Assurance certificate", title_style),
        Paragraph(
            f"{org_name} — {report.report_type} report for {report.period}",
            subtitle_style,
        ),
        Spacer(1, 6 * mm),
        Paragraph(
            "This certificate attests that a cryptographic commitment to every input "
            "of the accompanying report (<b>activity rows, emission factors, evidence "
            "files, methodology, and the PDF itself</b>) has been sealed. Any later "
            "change to any of those inputs will cause the Merkle root in this "
            "bundle to diverge from the on-chain record.",
            styles["Normal"],
        ),
        Spacer(1, 6 * mm),
    ]

    rows = [
        ["Sealed by", anchor.sealed_by],
        ["Sealed at", anchor.sealed_at.isoformat()],
        ["Chain", anchor.chain],
        ["Tx hash", anchor.tx_hash or "—"],
        ["Block", str(anchor.block_number) if anchor.block_number else "—"],
        ["Merkle root", anchor.merkle_root],
        ["Activity root", manifest.get("activity_root", "—")],
        ["Factor root", manifest.get("factor_root", "—")],
        ["Evidence root", manifest.get("evidence_root", "—")],
        ["Methodology hash", manifest.get("methodology_hash", "—")],
        ["PDF hash", manifest.get("pdf_hash", "—")],
    ]
    table_data = [[k, Paragraph(v, mono_style)] for k, v in rows]
    tbl = Table(table_data, colWidths=[40 * mm, 135 * mm])
    tbl.setStyle(
        TableStyle(
            [
                ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 9),
                ("TEXTCOLOR", (0, 0), (0, -1), slate),
                ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    flow.append(tbl)

    flow.extend(
        [
            Spacer(1, 8 * mm),
            Paragraph(
                f"Leaf counts — activity: {manifest.get('activity_leaf_count', 0)}, "
                f"factors: {manifest.get('factor_leaf_count', 0)}, "
                f"evidence: {manifest.get('evidence_leaf_count', 0)}",
                styles["Normal"],
            ),
            Spacer(1, 4 * mm),
            Paragraph(
                "To independently verify: unzip this bundle and run "
                "<font face='Courier'>python verify.py</font>. The recomputed root "
                "must match the Merkle root above. See README.md for details.",
                styles["Normal"],
            ),
        ]
    )

    doc.build(flow)
    return buf.getvalue()


_VERIFY_PY = '''#!/usr/bin/env python3
"""Standalone verifier for a CarbonLens assurance bundle.

Rebuilds the Merkle root from leaves.jsonl files + methodology.json + report.pdf
using only the Python standard library. Matches the recomputed root against
the one in manifest.json. Exit 0 on match, 1 on mismatch.

Usage:
    python verify.py [bundle_dir]        # default: current directory
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ZERO_HASH = "0" * 64


def sha256_str(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def merkle_root(leaves: list[str]) -> str:
    if not leaves:
        return ZERO_HASH
    layer = list(leaves)
    while len(layer) > 1:
        nxt = []
        for i in range(0, len(layer), 2):
            a = layer[i]
            b = layer[i + 1] if i + 1 < len(layer) else a
            nxt.append(sha256_str(a + b))
        layer = nxt
    return layer[0]


def load_jsonl(p: Path) -> list[dict]:
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


def main() -> int:
    root_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    manifest = json.loads((root_dir / "manifest.json").read_text())

    activity = load_jsonl(root_dir / "leaves" / "activity.jsonl")
    factors = load_jsonl(root_dir / "leaves" / "factors.jsonl")
    evidence = load_jsonl(root_dir / "leaves" / "evidence.jsonl")

    # Rehash payloads from scratch — do NOT trust the "leaf" field in jsonl.
    activity_leaves = sorted(sha256_str(x["payload"]) for x in activity)
    factor_leaves = sorted(sha256_str(x["payload"]) for x in factors)
    evidence_leaves = sorted(
        sha256_str(f"{x[\'path\']}:{x[\'file_hash\']}") for x in evidence
    )

    activity_root = merkle_root(activity_leaves)
    factor_root = merkle_root(factor_leaves)
    evidence_root = merkle_root(evidence_leaves)

    methodology = json.loads((root_dir / "methodology.json").read_text())
    methodology_hash = sha256_str(
        json.dumps(methodology, sort_keys=True, separators=(",", ":"))
    )

    pdf_path = root_dir / "report.pdf"
    pdf_hash = (
        file_sha256(pdf_path)
        if pdf_path.exists()
        else sha256_str(f"missing-pdf:report={manifest.get(\'report_id\', \'?\')}")
    )

    combined = "|".join(
        [activity_root, factor_root, evidence_root, methodology_hash, pdf_hash]
    )
    recomputed_root = "0x" + sha256_str(combined)

    stored_root = manifest["report_root"]
    ok = recomputed_root == stored_root

    def cmp(label: str, recomputed: str, stored: str) -> None:
        recomputed_pref = "0x" + recomputed if not recomputed.startswith("0x") else recomputed
        match = "OK " if recomputed_pref == stored else "BAD"
        print(f"  [{match}] {label}")
        print(f"         stored:     {stored}")
        print(f"         recomputed: {recomputed_pref}")

    print(f"Bundle: {root_dir.resolve()}")
    print(f"Report: {manifest.get(\'report_type\', \'?\')} / {manifest.get(\'period\', \'?\')}")
    print(f"Chain:  {manifest.get(\'chain\', \'?\')} tx={manifest.get(\'tx_hash\') or \'-\'}")
    print()
    cmp("activity_root", activity_root, manifest.get("activity_root", ""))
    cmp("factor_root", factor_root, manifest.get("factor_root", ""))
    cmp("evidence_root", evidence_root, manifest.get("evidence_root", ""))
    cmp("methodology_hash", methodology_hash, manifest.get("methodology_hash", ""))
    cmp("pdf_hash", pdf_hash, manifest.get("pdf_hash", ""))
    print()
    cmp("report_root", sha256_str(combined), stored_root)
    print()
    if ok:
        print("VERIFIED — this bundle matches the sealed root.")
        return 0
    print("MISMATCH — at least one subtree diverges. The bundle has been altered")
    print("or is paired with the wrong manifest.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
'''


_README = """# Assurance bundle — {org} / {report_type} / {period}

This zip is a self-contained proof that the accompanying report was sealed
with a specific set of inputs. An external auditor can run `verify.py` to
recompute the Merkle root and compare it to the on-chain commitment.

## Contents

- `manifest.json` — per-subtree roots, leaf counts, seal metadata.
- `methodology.json` — the methodology snapshot that was hashed at seal time.
- `leaves/activity.jsonl` — canonical payload per activity row.
- `leaves/factors.jsonl` — canonical payload per emission factor used.
- `leaves/evidence.jsonl` — evidence file paths + sha256 of their bytes.
- `report.pdf` — the sealed report PDF.
- `assurance_certificate.pdf` — one-page certificate with the root + chain info.
- `verify.py` — standalone verifier (Python 3.9+, stdlib only).

## How to verify

```
unzip assurance_<report_id>.zip -d assurance
cd assurance
python verify.py
```

The script rebuilds every subtree root from the leaves in this bundle,
re-hashes the PDF bytes, and combines them into the final `report_root`.
If the recomputed root matches `manifest.json`, the bundle is intact.

Chain: **{chain}**
Tx hash: `{tx_hash}`
Block: `{block_number}`

On-chain address (if deployed): query the `CarbonLensAnchor` contract with
`(orgId={org_id}, period="{period}")` and confirm the stored bytes32 matches
the Merkle root shown here (drop the `0x` prefix when comparing).
"""


def build_bundle(db: Session, report: Report, anchor: ReportAnchor) -> bytes:
    """Return the zip bytes for a sealed report's assurance bundle."""
    org = db.get(Organization, report.org_id)
    if org is None:
        raise ValueError(f"organization {report.org_id} not found")

    start, end = parse_period(report.period)
    manifest = json.loads(anchor.manifest)

    activity = _activity_lines(db, report.org_id, start, end)
    factors = _factor_lines(db, report.org_id, start, end)
    evidence = _evidence_lines(db, report.org_id, start, end)
    methodology = _methodology_snapshot(org, report.period)

    # Augment manifest with context the auditor needs for their report.
    manifest_out: dict[str, Any] = dict(manifest)
    manifest_out.update(
        {
            "report_id": report.id,
            "report_type": report.report_type,
            "period": report.period,
            "organization": org.name,
            "org_id": report.org_id,
            "sealed_by": anchor.sealed_by,
            "sealed_at": anchor.sealed_at.isoformat(),
            "chain": anchor.chain,
            "tx_hash": anchor.tx_hash,
            "block_number": anchor.block_number,
            "bundle_generated_at": datetime.utcnow().isoformat() + "Z",
        }
    )

    certificate = _certificate_pdf(report, org.name, anchor, manifest)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(manifest_out, indent=2, sort_keys=True))
        z.writestr(
            "methodology.json", json.dumps(methodology, indent=2, sort_keys=True)
        )
        z.writestr(
            "leaves/activity.jsonl",
            "\n".join(json.dumps(x, sort_keys=True) for x in activity),
        )
        z.writestr(
            "leaves/factors.jsonl",
            "\n".join(json.dumps(x, sort_keys=True) for x in factors),
        )
        z.writestr(
            "leaves/evidence.jsonl",
            "\n".join(json.dumps(x, sort_keys=True) for x in evidence),
        )
        if report.file_path and Path(report.file_path).exists():
            z.writestr("report.pdf", Path(report.file_path).read_bytes())
        z.writestr("assurance_certificate.pdf", certificate)
        z.writestr("verify.py", _VERIFY_PY)
        z.writestr(
            "README.md",
            _README.format(
                org=org.name,
                report_type=report.report_type,
                period=report.period,
                chain=anchor.chain,
                tx_hash=anchor.tx_hash or "-",
                block_number=anchor.block_number or "-",
                org_id=report.org_id,
            ),
        )
    return buf.getvalue()
