"""Lightweight in-place SQLite column migrator.

The project uses Alembic for new tables (see `alembic/`), but for adding
nullable columns to existing tables during demo/dev iteration this is
overkill. `ensure_columns()` inspects the live schema via PRAGMA and runs
`ALTER TABLE … ADD COLUMN …` only for missing columns.

SQLite-only. Safe to call on every startup.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine

# (table_name, column_name, column_ddl_fragment)
# DDL fragment must be valid SQLite ALTER TABLE ADD COLUMN syntax — no
# foreign keys, no unique constraints, nullable or with a defaulted value.
_NEW_COLUMNS: list[tuple[str, str, str]] = [
    # Board escalation workflow (Gap 1)
    ("anomaly_detections", "escalation_status", "VARCHAR(30)"),
    ("anomaly_detections", "escalation_owner", "VARCHAR(100)"),
    ("anomaly_detections", "escalation_due_date", "DATE"),
    ("anomaly_detections", "escalation_notes", "TEXT"),
    ("anomaly_detections", "escalated_at", "DATETIME"),
    ("anomaly_detections", "board_reviewed_at", "DATETIME"),
    # Carbon price (Gap 2)
    (
        "organizations",
        "carbon_price_inr_per_tonne",
        "FLOAT NOT NULL DEFAULT 2000.0",
    ),
    # Multi-tenant scoping — org_id on anomalies so queries can filter cleanly
    # without always joining facility. Nullable for SQLite ADD COLUMN; the
    # detector populates it on every scan and a one-time backfill runs below.
    ("anomaly_detections", "org_id", "INTEGER"),
    # Accountability — dept head bound to each activity row and defaulted
    # on each facility. Nullable on add; seed + handlers fill them in.
    ("facilities", "default_department_head_name", "VARCHAR(200)"),
    ("facilities", "default_department_head_email", "VARCHAR(200)"),
    ("activity_data", "department_head_name", "VARCHAR(200)"),
    ("activity_data", "department_head_email", "VARCHAR(200)"),
    # Tenant onboarding — fiscal year and onboarding-completion gate. New
    # seeded orgs land with onboarding_completed_at set (seed fills it in);
    # new signups land NULL and have to pass the /onboarding wizard.
    (
        "organizations",
        "fiscal_year_start_month",
        "INTEGER NOT NULL DEFAULT 4",
    ),
    ("organizations", "onboarding_completed_at", "DATETIME"),
]


def _existing_columns(conn, table: str) -> set[str]:
    rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return {r[1] for r in rows}


def _table_exists(conn, table: str) -> bool:
    r = conn.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name=:n"),
        {"n": table},
    ).fetchone()
    return r is not None


def ensure_columns(engine: Engine) -> list[str]:
    """Run ALTER TABLE ADD COLUMN for any column in `_NEW_COLUMNS` missing.

    Returns the list of DDLs executed (useful for logging). Idempotent.
    """
    executed: list[str] = []
    with engine.begin() as conn:
        for table, column, ddl in _NEW_COLUMNS:
            if not _table_exists(conn, table):
                continue  # table itself will be created by metadata.create_all
            if column in _existing_columns(conn, table):
                continue
            sql = f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"
            conn.execute(text(sql))
            executed.append(sql)

        # One-time backfill: mark already-existing orgs as onboarded so demo
        # users aren't redirected into the wizard on first boot post-migration.
        # Fresh signups via POST /orgs/signup land with NULL and have to finish
        # the wizard. New orgs created via the demo seeder also stamp this
        # explicitly.
        if _table_exists(conn, "organizations"):
            conn.execute(
                text(
                    "UPDATE organizations "
                    "SET onboarding_completed_at = COALESCE(onboarding_completed_at, created_at, CURRENT_TIMESTAMP) "
                    "WHERE onboarding_completed_at IS NULL"
                )
            )

        # One-time backfill: stamp org_id on existing anomalies via the facility
        # they reference. Anomalies without a facility (period_gap, etc.) fall
        # back to the only org present — multi-tenant rows are only seeded
        # after this migration runs, so this stays correct.
        if _table_exists(conn, "anomaly_detections"):
            conn.execute(
                text(
                    "UPDATE anomaly_detections "
                    "SET org_id = (SELECT org_id FROM facilities WHERE facilities.id = anomaly_detections.facility_id) "
                    "WHERE org_id IS NULL AND facility_id IS NOT NULL"
                )
            )
            conn.execute(
                text(
                    "UPDATE anomaly_detections "
                    "SET org_id = (SELECT id FROM organizations ORDER BY id LIMIT 1) "
                    "WHERE org_id IS NULL"
                )
            )
    return executed
