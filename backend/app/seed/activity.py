"""Seed 24 months (Jan 2024 – Dec 2025) of activity data across all 3 scopes.

Deterministic (seeded RNG) so re-runs produce identical data. Includes the
four intentional anomalies from the build spec for the anomaly-detector demo.
"""

import calendar
import random
from datetime import date

from sqlalchemy.orm import Session

from app.db.models import ActivityData, Facility, Organization

SEED = 42
START_YEAR = 2024
MONTHS = 24


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    _, last = calendar.monthrange(year, month)
    return date(year, month, 1), date(year, month, last)


def _month_list() -> list[tuple[date, date]]:
    out = []
    y, m = START_YEAR, 1
    for _ in range(MONTHS):
        out.append(_month_bounds(y, m))
        m += 1
        if m == 13:
            m = 1
            y += 1
    return out


def seed(db: Session, org: Organization) -> None:
    if (
        db.query(ActivityData)
        .join(Facility, ActivityData.facility_id == Facility.id)
        .filter(Facility.org_id == org.id)
        .count()
        > 0
    ):
        print("  activity data already seeded, skipping")
        return

    rng = random.Random(SEED)
    facilities = {f.name: f for f in org.facilities}
    pune = facilities["Pune Factory"]
    chennai = facilities["Chennai Factory"]
    mumbai = facilities["Mumbai Corporate Office"]

    months = _month_list()
    rows: list[ActivityData] = []

    # ── Scope 1 ─────────────────────────────────────────────────────────────
    for i, (start, end) in enumerate(months):
        is_summer = start.month in (4, 5, 6)

        # Pune DG diesel — higher in summer, ANOMALY spike in Sep 2024
        if start == date(2024, 9, 1):
            pune_dg = 12000  # intentional spike (anomaly #3)
        else:
            pune_dg = rng.randint(4000, 5000) if is_summer else rng.randint(3000, 4500)
        rows.append(_row(
            pune, 1, "fuel", "diesel", "DG set diesel consumption",
            pune_dg, "litres", start, end, f"DG_Log_{start:%Y%m}.pdf", 4, True,
        ))

        # Chennai natural gas — furnace
        rows.append(_row(
            chennai, 1, "fuel", "natural_gas", "Furnace natural gas consumption",
            rng.randint(8000, 12000), "m3", start, end, f"GasBill_{start:%Y%m}.pdf", 4, True,
        ))

        # Fleet diesel — per facility
        for fac in (pune, chennai, mumbai):
            rows.append(_row(
                fac, 1, "fuel", "diesel", "Company fleet diesel",
                rng.randint(1500, 2500), "litres", start, end,
                f"Fleet_{fac.name.split()[0]}_{start:%Y%m}.csv", 3, True,
            ))

        # Refrigerant top-up — quarterly (Mar, Jun, Sep, Dec)
        if start.month in (3, 6, 9, 12):
            rows.append(_row(
                pune, 1, "refrigerant", "r410a", "HVAC refrigerant top-up (R-410A)",
                15, "kg", start, end, f"HVAC_Service_{start:%Y%m}.pdf", 4, True,
            ))

    # ── Scope 2 ─────────────────────────────────────────────────────────────
    for i, (start, end) in enumerate(months):
        # Pune electricity — ANOMALY 3x in Jul 2024
        if start == date(2024, 7, 1):
            pune_kwh = 555000  # intentional data-entry error (anomaly #1)
        else:
            pune_kwh = rng.randint(150000, 220000)
        rows.append(_row(
            pune, 2, "electricity", "grid_india", "Grid electricity consumption",
            pune_kwh, "kWh", start, end, f"MSEB_{start:%Y%m}.pdf", 5, True,
        ))

        # Chennai electricity
        rows.append(_row(
            chennai, 2, "electricity", "grid_india", "Grid electricity consumption",
            rng.randint(120000, 180000), "kWh", start, end,
            f"TNEB_{start:%Y%m}.pdf", 5, True,
        ))

        # Mumbai electricity — MISSING Nov/Dec 2024 (anomaly #4)
        if start in (date(2024, 11, 1), date(2024, 12, 1)):
            continue
        rows.append(_row(
            mumbai, 2, "electricity", "grid_india", "Grid electricity consumption",
            rng.randint(25000, 35000), "kWh", start, end,
            f"Adani_{start:%Y%m}.pdf", 5, True,
        ))

    # ── Scope 3 ─────────────────────────────────────────────────────────────
    for start, end in months:
        # Cat 1 — purchased goods (reported against Pune as receiving plant)
        rows.append(_row(
            pune, 3, "material", "steel", "Steel procurement (Scope 3 Cat 1)",
            rng.randint(500, 800) * 1000, "kg", start, end,
            f"PO_Steel_{start:%Y%m}.xlsx", 3, False,
        ))
        rows.append(_row(
            pune, 3, "material", "aluminium", "Aluminium procurement (Scope 3 Cat 1)",
            rng.randint(50, 100) * 1000, "kg", start, end,
            f"PO_Al_{start:%Y%m}.xlsx", 3, False,
        ))
        rows.append(_row(
            pune, 3, "material", "plastics_general", "Plastics procurement (Scope 3 Cat 1)",
            rng.randint(30, 60) * 1000, "kg", start, end,
            f"PO_Plastic_{start:%Y%m}.xlsx", 3, False,
        ))

        # Cat 4 — upstream transport (road freight, tonne-km)
        rows.append(_row(
            pune, 3, "freight", "road_hgv", "Upstream road freight (Scope 3 Cat 4)",
            rng.randint(200000, 400000), "tonne-km", start, end,
            f"Freight_{start:%Y%m}.csv", 3, False,
        ))

        # Cat 6 — business travel
        domestic_flights = rng.randint(15, 30)
        rows.append(_row(
            mumbai, 3, "travel", "flight_domestic",
            f"Domestic business flights ({domestic_flights} trips, avg 1200km)",
            domestic_flights * 1200, "passenger-km", start, end,
            f"Travel_Dom_{start:%Y%m}.csv", 3, False,
        ))
        intl_flights = rng.randint(2, 5)
        rows.append(_row(
            mumbai, 3, "travel", "flight_international",
            f"International business flights ({intl_flights} trips, avg 6000km)",
            intl_flights * 6000, "passenger-km", start, end,
            f"Travel_Intl_{start:%Y%m}.csv", 3, False,
        ))
        rows.append(_row(
            mumbai, 3, "travel", "hotel_night", "Business hotel nights",
            rng.randint(30, 60), "night", start, end,
            f"Travel_Hotel_{start:%Y%m}.csv", 3, False,
        ))

        # Cat 7 — employee commute: 850 emp × 15km × 22 days × 2 legs
        commute_km = 850 * 15 * 22 * 2
        rows.append(_row(
            mumbai, 3, "commute", "car_petrol",
            "Employee commute (850 emp, ~15km one-way, 22 days/mo)",
            commute_km, "km", start, end,
            f"HR_Commute_Survey_{start:%Y%m}.xlsx", 2, False,
        ))

    db.add_all(rows)
    db.flush()
    print(f"  inserted {len(rows)} activity_data rows")
    print("  anomalies injected: Jul-2024 Pune electricity 3x, "
          "Sep-2024 Pune diesel spike, Nov/Dec-2024 Mumbai electricity missing")


def _row(
    facility: Facility,
    scope: int,
    category: str,
    subcategory: str,
    description: str,
    quantity: float,
    unit: str,
    period_start: date,
    period_end: date,
    source_doc: str,
    quality: int,
    verified: bool,
) -> ActivityData:
    return ActivityData(
        facility_id=facility.id,
        scope=scope,
        category=category,
        subcategory=subcategory,
        activity_description=description,
        quantity=float(quantity),
        unit=unit,
        period_start=period_start,
        period_end=period_end,
        source_document=source_doc,
        data_quality_score=quality,
        verified=verified,
        uploaded_by="seed",
        department_head_name=facility.default_department_head_name,
        department_head_email=facility.default_department_head_email,
    )
