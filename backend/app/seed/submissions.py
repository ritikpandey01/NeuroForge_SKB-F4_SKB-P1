"""Seed ~12 supplier submissions across recent periods, including one
intentionally zero-emission submission (anomaly #4 for Step 8).

Shape of `submitted_data` is intentionally loose JSON — the portal form
collects whatever the supplier reports. Step 10 (reports) and Step 8
(anomalies) only need period + aggregate emissions so they can flag
zero/absent reporting.
"""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.db.models import Organization, Supplier, SupplierSubmission

# (supplier_name, period, status, reported_emissions_tco2e, data_quality_score,
#  reviewed_offset_days | None)
# reviewed_offset_days None → pending (reviewed_at stays NULL).
_SUBMISSIONS: list[tuple[str, str, str, float, int, int | None]] = [
    # ── Tier-1, high-spend, high-maturity — the "good" suppliers ──
    ("SteelCorp India",        "2024-Q3", "accepted", 2850.0, 5, 7),
    ("SteelCorp India",        "2024-Q4", "accepted", 2910.0, 5, 5),
    ("Precision Parts Co",     "2024-Q3", "accepted",  420.0, 5, 6),
    ("Precision Parts Co",     "2024-Q4", "accepted",  445.0, 5, 4),
    ("TechBearings Ltd",       "2024-Q4", "accepted",  215.0, 4, 3),
    ("CopperLine Industries",  "2024-Q4", "flagged",   980.0, 3, 5),  # DQ flagged
    # ── Tier-1 logistics / activity-based ──
    ("FastFreight Logistics",  "2024-Q4", "accepted",  650.0, 4, 3),
    ("CastingWorks Pvt",       "2024-Q4", "pending",   310.0, 3, None),
    # ── Spend-based submissions (lower quality) ──
    ("MetalWorks Ltd",         "2024-Q4", "pending",   180.0, 2, None),
    ("PolyPack Solutions",     "2024-Q4", "pending",    95.0, 2, None),
    # ── Intentional anomalies (for Step 8 anomaly detector) ──
    ("ChemFlex Corp",          "2024-Q4", "pending",     0.0, 3, None),  # zero-emission anomaly
    ("MumbaiLogix",            "2024-Q4", "rejected",  1450.0, 1, 2),    # rejected: implausible
]


# UltraTech supplier submissions — major fuel/logistics partners report
# every FY24 quarter. Tonnage values are plausible for the spend/activity
# scale. Quarter labels use the "YYYY-QN" calendar convention (consistent
# with Greenfield). Volumes track the company's FY24 volume curve.
_ULTRATECH_SUBMISSIONS: list[tuple[str, str, str, float, int, int | None]] = [
    # ── Reliance Petcoke — top fuel supplier, reports all 4 quarters ──
    ("Reliance Petcoke",          "2023-Q2", "accepted", 1_180_000.0, 4, 9),
    ("Reliance Petcoke",          "2023-Q3", "accepted", 1_225_000.0, 4, 8),
    ("Reliance Petcoke",          "2024-Q3", "accepted", 1_250_000.0, 4, 10),
    ("Reliance Petcoke",          "2024-Q4", "accepted", 1_310_000.0, 4, 5),
    # ── Indian Oil Bulk Fuels — diesel + kiln fuels, quarterly ──
    ("Indian Oil Bulk Fuels",     "2023-Q2", "accepted",   640_000.0, 3, 7),
    ("Indian Oil Bulk Fuels",     "2023-Q3", "accepted",   655_000.0, 3, 6),
    ("Indian Oil Bulk Fuels",     "2024-Q3", "accepted",   670_000.0, 3, 8),
    ("Indian Oil Bulk Fuels",     "2024-Q4", "accepted",   680_000.0, 3, 6),
    # ── South Eastern Coalfields — Indian coal, Q2-Q4 only (Q1 late) ──
    ("South Eastern Coalfields",  "2023-Q3", "accepted",   515_000.0, 4, 5),
    ("South Eastern Coalfields",  "2024-Q3", "accepted",   528_000.0, 4, 6),
    ("South Eastern Coalfields",  "2024-Q4", "accepted",   540_000.0, 4, 4),
    # ── Limestone, ash, slag — raw inputs ──
    ("Gujarat Mineral Development","2023-Q3", "accepted",   11_800.0, 5, 5),
    ("Gujarat Mineral Development","2024-Q3", "accepted",   12_200.0, 5, 4),
    ("Gujarat Mineral Development","2024-Q4", "accepted",   12_500.0, 5, 3),
    ("NTPC Ash Utilization",      "2023-Q3", "accepted",    1_700.0, 4, 6),
    ("NTPC Ash Utilization",      "2024-Q3", "accepted",    1_750.0, 4, 5),
    ("NTPC Ash Utilization",      "2024-Q4", "accepted",    1_800.0, 4, 5),
    ("JSW Slag Supplies",         "2023-Q3", "accepted",    7_900.0, 3, 8),
    ("JSW Slag Supplies",         "2024-Q3", "flagged",     8_050.0, 3, 6),
    ("JSW Slag Supplies",         "2024-Q4", "flagged",     8_200.0, 3, 7),
    # ── CONCOR Rail — all 4 quarters (primary logistics partner) ──
    ("CONCOR Rail Logistics",     "2023-Q2", "accepted",   178_000.0, 5, 6),
    ("CONCOR Rail Logistics",     "2023-Q3", "accepted",   181_000.0, 5, 5),
    ("CONCOR Rail Logistics",     "2024-Q3", "accepted",   185_000.0, 5, 5),
    ("CONCOR Rail Logistics",     "2024-Q4", "accepted",   192_000.0, 5, 4),
    # ── TCI Freight — road logistics, quarterly ──
    ("TCI Freight Services",      "2023-Q3", "accepted",   118_000.0, 4, 7),
    ("TCI Freight Services",      "2024-Q3", "accepted",   120_000.0, 4, 6),
    ("TCI Freight Services",      "2024-Q4", "accepted",   122_000.0, 4, 6),
    # ── Adani Logistics + Delhivery — newer relationships, latest 2 Q ──
    ("Adani Logistics Bulk",      "2024-Q3", "accepted",   102_000.0, 3, 7),
    ("Adani Logistics Bulk",      "2024-Q4", "pending",    105_000.0, 3, None),
    ("Delhivery Road Haul",       "2024-Q3", "accepted",    37_000.0, 2, 8),
    ("Delhivery Road Haul",       "2024-Q4", "pending",     38_000.0, 2, None),
    # ── Smaller inputs — quarterly reporters, but lower DQ ──
    ("RefractoryLine India",      "2024-Q3", "pending",      2_350.0, 2, None),
    ("RefractoryLine India",      "2024-Q4", "pending",      2_400.0, 2, None),
    ("PackJute Industries",       "2024-Q3", "pending",      1_050.0, 2, None),
    ("PackJute Industries",       "2024-Q4", "pending",      1_100.0, 2, None),
    # ── Intentional anomalies for the detector ──
    ("BulkChem Additives",        "2024-Q3", "pending",          0.0, 2, None),  # zero Q3
    ("BulkChem Additives",        "2024-Q4", "pending",          0.0, 2, None),  # zero Q4
]


def seed(db: Session) -> None:
    now = datetime.utcnow()
    inserted = 0

    # Seed per-org so suppliers with duplicate-sounding names can't collide.
    for org in db.query(Organization).all():
        org_suppliers = {
            s.name: s for s in db.query(Supplier).filter_by(org_id=org.id).all()
        }
        payload = (
            _ULTRATECH_SUBMISSIONS if "UltraTech" in org.name else _SUBMISSIONS
        )
        # Per-(supplier, period) idempotency: rerunning adds missing pairs
        # without duplicating. Lets us extend this list over time.
        existing = {
            (row.supplier_id, row.period)
            for row in db.query(SupplierSubmission)
            .filter(SupplierSubmission.supplier_id.in_([s.id for s in org_suppliers.values()]))
            .all()
        }
        inserted += _seed_org_submissions(db, org_suppliers, payload, now, existing)

    db.flush()
    if inserted:
        print(f"  inserted {inserted} submissions across all orgs")
    else:
        print("  no new submissions (all supplier/period pairs already present)")


def _seed_org_submissions(
    db: Session,
    suppliers_by_name: dict[str, Supplier],
    payload: list[tuple[str, str, str, float, int, int | None]],
    now: datetime,
    existing_pairs: set[tuple[int, str]],
) -> int:
    inserted = 0
    for name, period, status, co2e_tonnes, dq, reviewed_offset in payload:
        supplier = suppliers_by_name.get(name)
        if not supplier:
            print(f"  WARN: supplier '{name}' not found; skipping submission")
            continue
        if (supplier.id, period) in existing_pairs:
            continue

        submitted_at = now - timedelta(days=14)
        reviewed_at = (
            submitted_at + timedelta(days=reviewed_offset)
            if reviewed_offset is not None
            else None
        )

        db.add(
            SupplierSubmission(
                supplier_id=supplier.id,
                period=period,
                submitted_data={
                    "total_emissions_tco2e": co2e_tonnes,
                    "scope": 3,
                    "scope3_category": supplier.scope3_category,
                    "methodology": (
                        "primary_activity_data"
                        if supplier.data_maturity_level == "verified_primary"
                        else "supplier_specific"
                        if supplier.data_maturity_level == "activity_based"
                        else "spend_based_eeio"
                    ),
                    "notes": (
                        "zero emissions reported — requires verification"
                        if co2e_tonnes == 0.0
                        else None
                    ),
                },
                data_quality_score=dq,
                status=status,
                submitted_at=submitted_at,
                reviewed_at=reviewed_at,
            )
        )
        inserted += 1

    return inserted
