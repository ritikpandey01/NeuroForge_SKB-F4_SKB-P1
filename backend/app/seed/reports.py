"""Seed pre-generated reports for both orgs.

Demo users shouldn't have to wait through a first report generation to
see the module — ship with a handful already rendered to PDF + committed
to the `reports` table.

Per-(org, report_type, period) idempotent: reruns skip any combination
that already exists.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import Organization, Report
from app.services.report_renderer import build_context, render_pdf


# (org_name_prefix, framework, period)
# `parse_period("FY2024")` → Apr 2024 – Mar 2025 (start-year convention).
# So UltraTech activity year 2023 → "FY2023", Greenfield year 2024 → "FY2024".
_TARGETS: list[tuple[str, str, str]] = [
    ("Greenfield", "BRSR", "FY2024"),
    ("Greenfield", "BRSR", "FY2025"),
    ("UltraTech", "BRSR", "FY2022"),
    ("UltraTech", "BRSR", "FY2023"),
    ("UltraTech", "GRI", "FY2023"),
    ("UltraTech", "TCFD", "FY2023"),
]


def seed(db: Session) -> None:
    orgs = {o.name: o for o in db.query(Organization).all()}
    inserted = 0

    for prefix, framework, period in _TARGETS:
        org = next((o for name, o in orgs.items() if name.startswith(prefix)), None)
        if org is None:
            continue

        existing = (
            db.query(Report)
            .filter_by(org_id=org.id, report_type=framework, period=period)
            .first()
        )
        if existing is not None:
            continue

        report = Report(
            org_id=org.id,
            report_type=framework,
            period=period,
            status="generating",
        )
        db.add(report)
        db.flush()

        try:
            ctx = build_context(db, period, org_id=org.id)
        except ValueError as e:
            # Most likely cause: no activity data for that period. Skip the
            # row rather than leaving a "failed" Report behind.
            print(f"  skip {org.name}/{framework}/{period}: {e}")
            db.delete(report)
            continue

        try:
            path = render_pdf(
                framework=framework,
                period=period,
                context=ctx,
                narrative=None,
                report_id=report.id,
            )
        except Exception as e:
            print(f"  render failed for {org.name}/{framework}/{period}: {e}")
            report.status = "failed"
            continue

        report.file_path = str(path)
        report.status = "ready"
        inserted += 1
        print(f"  seeded {org.name} / {framework} / {period}")

    db.flush()
    if inserted == 0:
        print("  no new reports (all targets already present)")
    else:
        print(f"  generated {inserted} report PDFs")
