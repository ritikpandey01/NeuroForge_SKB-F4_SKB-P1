"""GHG calculation engine (Module 2).

Factor resolution order:
    1. exact:     category + subcategory + region + year
    2. region:    category + subcategory + region (most recent year)
    3. global:    category + subcategory (any region, most recent year)
    4. otherwise: raise FactorNotFound — never silently pick a wrong factor.

Formula (all scopes):
    co2e_kg = quantity * factor_value
(unit conversion is assumed baked into the stored factor's unit; the engine
validates that activity.unit is compatible with factor.unit.)
"""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ActivityData, Emission, EmissionFactor


class FactorNotFound(Exception):
    def __init__(self, category: str, subcategory: str):
        super().__init__(f"No emission factor for {category}/{subcategory}")
        self.category = category
        self.subcategory = subcategory


@dataclass
class CalcResult:
    emission_id: int
    activity_id: int
    factor_id: int
    co2e_kg: float
    method: str


# Units where factor.unit = "kgCO2e/<unit>". Listed here because we trust the
# emission-factor library; the activity.unit just needs to equal the factor's
# denominator (e.g., activity unit "kWh" → factor unit "kgCO2e/kWh").
def _factor_denominator(factor_unit: str) -> str:
    # "kgCO2e/kWh" → "kWh"
    return factor_unit.split("/", 1)[1] if "/" in factor_unit else factor_unit


def _normalize_unit(u: str) -> str:
    u = u.lower().strip().replace("³", "3").replace("²", "2")
    aliases = {
        "liter": "litre",
        "liters": "litre",
        "litres": "litre",
        "kilogram": "kg",
        "kilograms": "kg",
        "kgs": "kg",
        "nights": "night",
        "kms": "km",
        "tonne_km": "tonne-km",
        "passenger_km": "passenger-km",
    }
    if u in aliases:
        return aliases[u]
    if u.endswith("s") and not u.endswith("ss") and len(u) > 2:
        return u[:-1]
    return u


def _units_compatible(activity_unit: str, factor_unit: str) -> bool:
    return _normalize_unit(activity_unit) == _normalize_unit(_factor_denominator(factor_unit))


def resolve_factor(
    db: Session,
    category: str,
    subcategory: str,
    region: str = "IN",
    year: int | None = None,
) -> EmissionFactor:
    """Return the best-matching emission factor, or raise FactorNotFound."""
    base = select(EmissionFactor).where(
        EmissionFactor.category == category,
        EmissionFactor.subcategory == subcategory,
    )

    if year is not None:
        exact = db.scalars(
            base.where(EmissionFactor.region == region, EmissionFactor.year == year)
        ).first()
        if exact:
            return exact

    regional = db.scalars(
        base.where(EmissionFactor.region == region).order_by(EmissionFactor.year.desc())
    ).first()
    if regional:
        return regional

    global_ = db.scalars(
        base.where(EmissionFactor.region == "GLOBAL").order_by(EmissionFactor.year.desc())
    ).first()
    if global_:
        return global_

    any_match = db.scalars(base.order_by(EmissionFactor.year.desc())).first()
    if any_match:
        return any_match

    raise FactorNotFound(category, subcategory)


def _methodology_note(scope: int, activity: ActivityData, factor: EmissionFactor) -> str:
    basis = {
        1: "Direct measurement (fuel/refrigerant × emission factor)",
        2: "Location-based grid electricity (kWh × grid factor)",
        3: "Activity-based (quantity × published factor)",
    }.get(scope, "Activity-based")
    return (
        f"Scope {scope} — {basis}. "
        f"Formula: {activity.quantity} {activity.unit} × {factor.factor_value} "
        f"{factor.unit} = {activity.quantity * factor.factor_value:.2f} kgCO2e. "
        f"Source: {factor.source} {factor.year} ({factor.region})."
    )


def calculate_for_activity(
    db: Session, activity: ActivityData, *, region_hint: str = "IN"
) -> CalcResult:
    """Idempotent: if an Emission already exists for this activity, return it."""
    existing = db.scalars(
        select(Emission).where(Emission.activity_data_id == activity.id)
    ).first()
    if existing:
        return CalcResult(
            emission_id=existing.id,
            activity_id=activity.id,
            factor_id=existing.emission_factor_id or 0,
            co2e_kg=existing.co2e_kg,
            method=existing.calculation_method,
        )

    factor = resolve_factor(
        db,
        category=activity.category,
        subcategory=activity.subcategory,
        region=region_hint,
        year=activity.period_start.year if activity.period_start else None,
    )

    if not _units_compatible(activity.unit, factor.unit):
        # Not fatal — we still compute, but flag it in the method string so the
        # UI can surface the mismatch. Prevents silent wrong conversions.
        method_prefix = f"[UNIT MISMATCH: activity '{activity.unit}' vs factor '{factor.unit}'] "
    else:
        method_prefix = ""

    co2e = float(activity.quantity) * float(factor.factor_value)
    method = method_prefix + _methodology_note(activity.scope, activity, factor)

    emission = Emission(
        activity_data_id=activity.id,
        scope=activity.scope,
        category=activity.category,
        co2e_kg=co2e,
        calculation_method=method,
        emission_factor_id=factor.id,
    )
    db.add(emission)
    db.flush()

    return CalcResult(
        emission_id=emission.id,
        activity_id=activity.id,
        factor_id=factor.id,
        co2e_kg=co2e,
        method=method,
    )


def calculate_batch(
    db: Session,
    *,
    activity_ids: list[int] | None = None,
    facility_id: int | None = None,
    scope: int | None = None,
    region_hint: str = "IN",
    org_id: int | None = None,
) -> dict:
    """Calculate emissions for a filtered batch.

    If activity_ids is None, calculates for every activity_data row matching
    the optional facility_id / scope filters. `org_id`, when set, joins
    through Facility to prevent calculating across tenants.
    """
    from app.db.models import Facility

    stmt = select(ActivityData)
    if org_id is not None:
        stmt = stmt.join(Facility, ActivityData.facility_id == Facility.id).where(
            Facility.org_id == org_id
        )
    if activity_ids:
        stmt = stmt.where(ActivityData.id.in_(activity_ids))
    if facility_id:
        stmt = stmt.where(ActivityData.facility_id == facility_id)
    if scope:
        stmt = stmt.where(ActivityData.scope == scope)

    activities = list(db.scalars(stmt).all())

    computed = 0
    skipped = 0
    errors: list[dict] = []
    total_kg = 0.0

    for a in activities:
        try:
            before = db.scalars(
                select(Emission).where(Emission.activity_data_id == a.id)
            ).first()
            res = calculate_for_activity(db, a, region_hint=region_hint)
            total_kg += res.co2e_kg
            if before is None:
                computed += 1
            else:
                skipped += 1
        except FactorNotFound as e:
            errors.append({"activity_id": a.id, "error": str(e)})

    return {
        "activities_seen": len(activities),
        "computed": computed,
        "already_had_emission": skipped,
        "errors": errors,
        "total_co2e_kg": total_kg,
    }
