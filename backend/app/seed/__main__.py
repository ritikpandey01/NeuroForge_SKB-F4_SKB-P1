"""Seed the CarbonLens demo database.

Run with (from the backend/ directory):
    python -m app.seed
"""

from app.db import models  # noqa: F401 — register models on metadata
from app.db.base import Base
from app.db.migrate_inplace import ensure_columns
from app.db.session import SessionLocal, engine
from app.seed import (
    activity,
    activity_ultratech,
    audit,
    company,
    escalations,
    factors,
    reports,
    submissions,
    suppliers,
    users,
)
from app.services.anomaly_detector import run_scan
from app.services.calculation_engine import calculate_batch


def main() -> None:
    print("Creating tables (if missing)...")
    Base.metadata.create_all(engine)

    print("Applying in-place column migrations...")
    added = ensure_columns(engine)
    for sql in added:
        print(f"  {sql}")
    if not added:
        print("  up to date")

    db = SessionLocal()
    try:
        print("Seeding emission factors...")
        factors.seed(db)

        # ── Greenfield (synthetic demo org) ──────────────────────────────
        print("Seeding Greenfield organization + facilities...")
        greenfield = company.seed(db)

        print("Seeding Greenfield suppliers...")
        suppliers.seed(db, greenfield)

        print("Seeding Greenfield activity data (24 months)...")
        activity.seed(db, greenfield)

        # ── UltraTech (real published-data org) ──────────────────────────
        print("Seeding UltraTech organization + facilities...")
        ultratech = company.seed_ultratech(db)

        print("Seeding UltraTech suppliers...")
        suppliers.seed_ultratech(db, ultratech)

        print("Seeding UltraTech FY24 activity data...")
        activity_ultratech.seed(db, ultratech)

        # ── Shared: submissions, users, calculations, audits, anomalies ──
        print("Seeding supplier submissions (both orgs)...")
        submissions.seed(db)

        print("Seeding demo users (both orgs)...")
        users.seed_for(db, greenfield)
        users.seed_for(db, ultratech)

        for org in (greenfield, ultratech):
            print(f"Calculating emissions for {org.name}...")
            result = calculate_batch(db, org_id=org.id)
            print(
                f"  computed {result['computed']}, "
                f"pre-existing {result['already_had_emission']}, "
                f"errors {len(result['errors'])}, "
                f"total {result['total_co2e_kg'] / 1000:,.1f} tCO2e"
            )

        for org in (greenfield, ultratech):
            print(f"Running anomaly scan for {org.name}...")
            scan = run_scan(db, org_id=org.id)
            print(
                f"  detected {scan['total_detected']} "
                f"({scan['new']} new, {scan['updated']} refreshed)"
            )

        print("Seeding report PDFs (both orgs)...")
        reports.seed(db)

        print("Seeding audit log history (both orgs)...")
        audit.seed(db)

        print("Seeding board escalations...")
        escalations.seed(db)

        db.commit()
        print("\n✓ Seed complete.")
        users.print_login_cheatsheet([greenfield, ultratech])
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
