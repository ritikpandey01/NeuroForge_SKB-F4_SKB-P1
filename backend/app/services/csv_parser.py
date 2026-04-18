"""CSV ingest for activity data (Module 5).

Expected columns (header row required, case-insensitive, order-independent):
    facility_name, scope, category, subcategory, activity_description,
    quantity, unit, period_start, period_end[, source_document, data_quality_score]

Dates accepted: YYYY-MM-DD or YYYY-MM (interpreted as month start/end).
"""

from __future__ import annotations

import calendar
import csv
import io
from dataclasses import dataclass, field
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Facility
from app.services.validation import validate_activity

REQUIRED_COLS = {
    "facility_name",
    "scope",
    "category",
    "subcategory",
    "activity_description",
    "quantity",
    "unit",
    "period_start",
    "period_end",
}
OPTIONAL_COLS = {"source_document", "data_quality_score"}


@dataclass
class ParsedRow:
    row_number: int  # 1-based, includes header offset (so first data row = 2)
    raw: dict
    parsed: dict | None = None  # ready-to-insert dict; None if errors block it
    issues: list[dict] = field(default_factory=list)


@dataclass
class CsvParseResult:
    rows: list[ParsedRow]
    summary: dict

    def to_dict(self) -> dict:
        return {
            "summary": self.summary,
            "rows": [
                {
                    "row_number": r.row_number,
                    "raw": r.raw,
                    "parsed": r.parsed,
                    "issues": r.issues,
                }
                for r in self.rows
            ],
        }


def _parse_date(value: str, *, end_of_month: bool = False) -> date:
    s = value.strip()
    if len(s) == 7 and s[4] == "-":  # YYYY-MM
        y, m = int(s[:4]), int(s[5:])
        if end_of_month:
            return date(y, m, calendar.monthrange(y, m)[1])
        return date(y, m, 1)
    return date.fromisoformat(s)


def _normalize_header(h: str) -> str:
    return h.strip().lower().replace(" ", "_")


def parse_csv(
    db: Session,
    *,
    file_bytes: bytes,
    uploaded_by: str | None = None,
    org_id: int | None = None,
) -> CsvParseResult:
    text = file_bytes.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))

    if not reader.fieldnames:
        return CsvParseResult(rows=[], summary={"error": "empty file or no header row"})

    fieldmap = {_normalize_header(h): h for h in reader.fieldnames}
    missing = REQUIRED_COLS - set(fieldmap)
    if missing:
        return CsvParseResult(
            rows=[],
            summary={
                "error": f"missing required columns: {sorted(missing)}",
                "required": sorted(REQUIRED_COLS),
                "optional": sorted(OPTIONAL_COLS),
            },
        )

    fac_stmt = select(Facility)
    if org_id is not None:
        fac_stmt = fac_stmt.where(Facility.org_id == org_id)
    facilities = {f.name.strip().lower(): f for f in db.scalars(fac_stmt).all()}

    rows: list[ParsedRow] = []
    for idx, raw in enumerate(reader, start=2):
        norm = {_normalize_header(k): (v or "").strip() for k, v in raw.items()}
        row = ParsedRow(row_number=idx, raw=norm)

        try:
            facility_name = norm["facility_name"]
            facility = facilities.get(facility_name.lower())
            if not facility:
                row.issues.append(
                    {
                        "severity": "error",
                        "field": "facility_name",
                        "message": f"unknown facility '{facility_name}'",
                    }
                )

            scope = int(norm["scope"])
            quantity = float(norm["quantity"])
            period_start = _parse_date(norm["period_start"])
            period_end = _parse_date(norm["period_end"], end_of_month=True)
            dq = int(norm["data_quality_score"]) if norm.get("data_quality_score") else 3

            if not facility:
                rows.append(row)
                continue

            v = validate_activity(
                db,
                facility_id=facility.id,
                scope=scope,
                category=norm["category"],
                subcategory=norm["subcategory"],
                quantity=quantity,
                unit=norm["unit"],
                period_start=period_start,
                period_end=period_end,
            )
            row.issues.extend(
                {"severity": i.severity, "field": i.field, "message": i.message}
                for i in v.issues
            )

            row.parsed = {
                "facility_id": facility.id,
                "scope": scope,
                "category": norm["category"],
                "subcategory": norm["subcategory"],
                "activity_description": norm["activity_description"],
                "quantity": quantity,
                "unit": norm["unit"],
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "source_document": norm.get("source_document") or None,
                "data_quality_score": dq,
                "uploaded_by": uploaded_by,
            }
        except (ValueError, KeyError) as e:
            row.issues.append(
                {"severity": "error", "field": "row", "message": f"parse error: {e}"}
            )

        rows.append(row)

    summary = {
        "total_rows": len(rows),
        "rows_with_errors": sum(
            1 for r in rows if any(i["severity"] == "error" for i in r.issues)
        ),
        "rows_with_warnings": sum(
            1 for r in rows if any(i["severity"] == "warning" for i in r.issues)
        ),
        "rows_ready": sum(
            1
            for r in rows
            if r.parsed is not None and not any(i["severity"] == "error" for i in r.issues)
        ),
    }
    return CsvParseResult(rows=rows, summary=summary)
