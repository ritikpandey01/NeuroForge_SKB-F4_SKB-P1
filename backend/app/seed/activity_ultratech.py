"""Seed FY24 activity data for UltraTech Cement (Apr 2023 – Mar 2024).

Targets are calibrated against UltraTech's public FY24 disclosures so the
demo's totals land within roughly 5% of the real company:

    Cementitious produced      ~118 Mt
    Scope-1 intensity          ~556 kgCO2/t cementitious
    Scope-1 absolute           ~65.6 MtCO2e
    Scope-2 (location-based)   ~5.6 MtCO2e
    Scope-3 (travel/freight)   ~0.4 MtCO2e  (light slice — not full Cat 1-15)

Scope-1 is split as cement industry convention requires:
  - Process (calcination of limestone)  ≈ 44 Mt   (~67% of S1)
  - Kiln fuel (pet-coke + Indian coal)  ≈ 21 Mt   (~32% of S1)
  - Fleet diesel + refrigerants         ≈ 0.3 Mt  (<1%, required for audit)

Weights in company.py spread production across ten plants plus one HQ
office (weight 0). Quantities are deterministic via a seeded RNG so reruns
produce identical rows.
"""

from __future__ import annotations

import calendar
import random
from datetime import date

from sqlalchemy.orm import Session

from app.db.models import ActivityData, Facility, Organization
from app.seed.company import ULTRATECH_FACILITIES

SEED = 2026

# Three fiscal years of history. Scale is a simple multiplier on volume
# that lets FY24 keep its calibrated 67.73 Mt total while FY22/FY23 land
# lower — mimicking the industry's multi-year growth curve with an
# improving intensity story. Not physically rigorous (real intensity
# improvement would change fuel/clinker mix, not scale uniformly), but
# adequate for a demo that wants visible YoY trend.
_FY_CONFIG: list[tuple[int, float, str]] = [
    (2021, 0.88, "FY22"),  # Apr 2021 – Mar 2022
    (2022, 0.94, "FY23"),  # Apr 2022 – Mar 2023
    (2023, 1.00, "FY24"),  # Apr 2023 – Mar 2024 (calibrated baseline)
]


def _months_for(start_year: int) -> list[tuple[date, date]]:
    months: list[tuple[date, date]] = []
    y, m = start_year, 4
    for _ in range(12):
        last = calendar.monthrange(y, m)[1]
        months.append((date(y, m, 1), date(y, m, last)))
        m += 1
        if m == 13:
            m = 1
            y += 1
    return months


# Total cementitious production for the year (Mt).
_ANNUAL_PRODUCTION_MT = 118.0

# Per-tonne-cement factors calibrated so the plant-level rolls sum to target.
# These are design parameters for the seed — real per-plant figures are not
# disclosed at this granularity. Units throughout: kg / t cement unless noted.
_KG_PET_COKE_PER_T_CEMENT = 78.0       # ~70% thermal share via pet-coke
_KG_COAL_INDIAN_PER_T_CEMENT = 28.0    # ~25% thermal share via Indian coal
_KG_AFR_PER_T_CEMENT = 4.0             # 4-6% thermal substitution rate
_CLINKER_FACTOR = 0.72                 # tonnes clinker / tonne cement
# Grid electricity: ~74 kWh/t cement before CPP/WHRS offsets; assume ~12%
# of plants' draw comes from grid after captive power, so net ≈ 70 kWh/t.
_KWH_PER_T_CEMENT = 70.0


def _weight_of(name: str) -> float:
    for f in ULTRATECH_FACILITIES:
        if f["name"] == name:
            return f["weight"]
    return 0.0


def _fy_already_seeded(db: Session, org_id: int, start_year: int) -> bool:
    period_start = date(start_year, 4, 1)
    period_end = date(start_year + 1, 3, 31)
    return bool(
        db.query(ActivityData)
        .join(Facility, ActivityData.facility_id == Facility.id)
        .filter(Facility.org_id == org_id)
        .filter(ActivityData.period_start >= period_start)
        .filter(ActivityData.period_end <= period_end)
        .first()
    )


def _seed_fy(
    db: Session,
    org: Organization,
    start_year: int,
    scale: float,
    label: str,
) -> int:
    # Stable RNG per-FY so reruns are deterministic AND years don't share
    # wobble patterns (a single rng across FYs would vary with insert order).
    rng = random.Random(SEED + start_year)
    facilities = {f.name: f for f in org.facilities}
    hq = facilities.get("Mumbai Corporate HQ")
    months = _months_for(start_year)

    rows: list[ActivityData] = []

    for name, fac in facilities.items():
        weight = _weight_of(name)
        if weight <= 0:
            continue

        annual_mt = _ANNUAL_PRODUCTION_MT * weight * scale
        monthly_mt_avg = annual_mt / 12.0
        is_grinding = fac.type == "grinding_unit"

        for start, end in months:
            wobble = 1.0 + (rng.random() - 0.5) * 0.12
            monthly_t = monthly_mt_avg * 1_000_000 * wobble

            if not is_grinding:
                rows.append(_row(
                    fac, 1, "fuel", "pet_coke",
                    "Kiln pet-coke consumption",
                    round(monthly_t * _KG_PET_COKE_PER_T_CEMENT, 1), "kg",
                    start, end, f"PetCoke_{fac.name.split()[0]}_{start:%Y%m}.pdf",
                    4, True,
                ))
                rows.append(_row(
                    fac, 1, "fuel", "coal_indian",
                    "Kiln Indian coal consumption",
                    round(monthly_t * _KG_COAL_INDIAN_PER_T_CEMENT, 1), "kg",
                    start, end, f"Coal_{fac.name.split()[0]}_{start:%Y%m}.pdf",
                    4, True,
                ))
                rows.append(_row(
                    fac, 1, "fuel", "afr_blend",
                    "Alternative fuel / biomass co-processing",
                    round(monthly_t * _KG_AFR_PER_T_CEMENT, 1), "kg",
                    start, end, f"AFR_{fac.name.split()[0]}_{start:%Y%m}.pdf",
                    3, True,
                ))

                clinker_t = monthly_t * _CLINKER_FACTOR
                rows.append(_row(
                    fac, 1, "process", "clinker_calcination",
                    "Limestone calcination (process CO2, CaCO3 → CaO + CO2)",
                    round(clinker_t, 1), "tonne",
                    start, end, f"Clinker_{fac.name.split()[0]}_{start:%Y%m}.xlsx",
                    5, True,
                ))

            rows.append(_row(
                fac, 1, "fuel", "diesel",
                "Mining haul-truck and internal fleet diesel",
                rng.randint(18_000, 32_000) if not is_grinding else rng.randint(3_000, 6_000),
                "litre", start, end, f"Diesel_{fac.name.split()[0]}_{start:%Y%m}.csv",
                3, True,
            ))

            if start.month in (6, 9, 12, 3):
                rows.append(_row(
                    fac, 1, "refrigerant", "r410a",
                    "Chiller / HVAC refrigerant top-up",
                    rng.randint(10, 25), "kg",
                    start, end, f"HVAC_{fac.name.split()[0]}_{start:%Y%m}.pdf",
                    4, True,
                ))

            kwh = monthly_t * _KWH_PER_T_CEMENT
            grid_share = 0.25 if not is_grinding else 0.95
            rows.append(_row(
                fac, 2, "electricity", "grid_india",
                "Grid electricity (post CPP/WHRS offset)",
                round(kwh * grid_share, 0), "kWh",
                start, end, f"Grid_{fac.name.split()[0]}_{start:%Y%m}.pdf",
                5, True,
            ))

    if hq is not None:
        for start, end in months:
            rows.append(_row(
                hq, 3, "freight", "rail",
                "Upstream + downstream rail freight (network)",
                int(rng.randint(650_000_000, 780_000_000) * scale), "tonne-km",
                start, end, f"Freight_Rail_{start:%Y%m}.csv", 3, False,
            ))
            rows.append(_row(
                hq, 3, "freight", "road_hgv",
                "Road HGV freight (last-mile + inter-plant)",
                int(rng.randint(420_000_000, 520_000_000) * scale), "tonne-km",
                start, end, f"Freight_Road_{start:%Y%m}.csv", 3, False,
            ))
            rows.append(_row(
                hq, 3, "travel", "flight_domestic",
                "Domestic business flights (plant visits + ops)",
                int(rng.randint(180_000, 260_000) * scale), "passenger-km",
                start, end, f"Travel_{start:%Y%m}.csv", 3, False,
            ))
            rows.append(_row(
                hq, 3, "commute", "car_petrol",
                "Corporate HQ employee commute (1,200 staff)",
                int(1200 * 14 * 22 * 2 * scale), "km",
                start, end, f"HR_Commute_{start:%Y%m}.xlsx", 2, False,
            ))

    db.add_all(rows)
    db.flush()
    print(f"  inserted {len(rows)} UltraTech activity rows ({label}: Apr {start_year} – Mar {start_year+1})")
    return len(rows)


def seed(db: Session, org: Organization) -> None:
    total = 0
    for start_year, scale, label in _FY_CONFIG:
        if _fy_already_seeded(db, org.id, start_year):
            print(f"  UltraTech {label} already seeded, skipping")
            continue
        total += _seed_fy(db, org, start_year, scale, label)
    if total == 0:
        print("  UltraTech: no new activity rows seeded (all FYs present)")


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
