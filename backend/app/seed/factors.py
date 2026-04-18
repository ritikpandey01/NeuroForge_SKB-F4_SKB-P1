"""Seed ~50 emission factors covering India and global defaults (CEA/DEFRA/EPA/IPCC)."""

from sqlalchemy.orm import Session

from app.db.models import EmissionFactor

FACTORS: list[dict] = [
    # Electricity grids
    {"category": "electricity", "subcategory": "grid_india", "factor_value": 0.716,
     "unit": "kgCO2e/kWh", "source": "CEA", "region": "IN", "year": 2023},
    {"category": "electricity", "subcategory": "grid_usa", "factor_value": 0.389,
     "unit": "kgCO2e/kWh", "source": "EPA", "region": "US", "year": 2023},
    {"category": "electricity", "subcategory": "grid_uk", "factor_value": 0.233,
     "unit": "kgCO2e/kWh", "source": "DEFRA", "region": "UK", "year": 2023},
    {"category": "electricity", "subcategory": "solar_ppa", "factor_value": 0.045,
     "unit": "kgCO2e/kWh", "source": "IPCC", "region": "GLOBAL", "year": 2023},
    {"category": "electricity", "subcategory": "wind_ppa", "factor_value": 0.011,
     "unit": "kgCO2e/kWh", "source": "IPCC", "region": "GLOBAL", "year": 2023},

    # Stationary / mobile fuels
    {"category": "fuel", "subcategory": "diesel", "factor_value": 2.68,
     "unit": "kgCO2e/litre", "source": "DEFRA", "region": "GLOBAL", "year": 2023},
    {"category": "fuel", "subcategory": "petrol", "factor_value": 2.31,
     "unit": "kgCO2e/litre", "source": "DEFRA", "region": "GLOBAL", "year": 2023},
    {"category": "fuel", "subcategory": "natural_gas", "factor_value": 2.02,
     "unit": "kgCO2e/m3", "source": "DEFRA", "region": "GLOBAL", "year": 2023},
    {"category": "fuel", "subcategory": "lpg", "factor_value": 1.56,
     "unit": "kgCO2e/litre", "source": "DEFRA", "region": "GLOBAL", "year": 2023},
    {"category": "fuel", "subcategory": "cng", "factor_value": 2.02,
     "unit": "kgCO2e/kg", "source": "DEFRA", "region": "GLOBAL", "year": 2023},
    {"category": "fuel", "subcategory": "kerosene", "factor_value": 2.52,
     "unit": "kgCO2e/litre", "source": "DEFRA", "region": "GLOBAL", "year": 2023},
    {"category": "fuel", "subcategory": "furnace_oil", "factor_value": 3.15,
     "unit": "kgCO2e/litre", "source": "IPCC", "region": "GLOBAL", "year": 2023},
    {"category": "fuel", "subcategory": "coal_bituminous", "factor_value": 2.42,
     "unit": "kgCO2e/kg", "source": "IPCC", "region": "GLOBAL", "year": 2023},
    {"category": "fuel", "subcategory": "coal_indian", "factor_value": 2.10,
     "unit": "kgCO2e/kg", "source": "CPCB", "region": "IN", "year": 2023},
    {"category": "fuel", "subcategory": "pet_coke", "factor_value": 3.20,
     "unit": "kgCO2e/kg", "source": "IPCC", "region": "GLOBAL", "year": 2023},
    {"category": "fuel", "subcategory": "afr_blend", "factor_value": 1.10,
     "unit": "kgCO2e/kg", "source": "GNR", "region": "GLOBAL", "year": 2023},

    # Cement industry — process emissions (calcination of limestone: CaCO3 → CaO + CO2)
    {"category": "process", "subcategory": "clinker_calcination", "factor_value": 525.0,
     "unit": "kgCO2e/tonne", "source": "GNR", "region": "GLOBAL", "year": 2023},

    # Refrigerants (GWP = kgCO2e per kg of refrigerant released)
    {"category": "refrigerant", "subcategory": "r410a", "factor_value": 2088.0,
     "unit": "kgCO2e/kg", "source": "IPCC", "region": "GLOBAL", "year": 2023},
    {"category": "refrigerant", "subcategory": "r134a", "factor_value": 1430.0,
     "unit": "kgCO2e/kg", "source": "IPCC", "region": "GLOBAL", "year": 2023},
    {"category": "refrigerant", "subcategory": "r22", "factor_value": 1810.0,
     "unit": "kgCO2e/kg", "source": "IPCC", "region": "GLOBAL", "year": 2023},
    {"category": "refrigerant", "subcategory": "r32", "factor_value": 675.0,
     "unit": "kgCO2e/kg", "source": "IPCC", "region": "GLOBAL", "year": 2023},

    # Materials (purchased goods — Scope 3 Cat 1)
    {"category": "material", "subcategory": "steel", "factor_value": 1.85,
     "unit": "kgCO2e/kg", "source": "DEFRA", "region": "GLOBAL", "year": 2023},
    {"category": "material", "subcategory": "aluminium", "factor_value": 8.24,
     "unit": "kgCO2e/kg", "source": "DEFRA", "region": "GLOBAL", "year": 2023},
    {"category": "material", "subcategory": "plastics_general", "factor_value": 3.12,
     "unit": "kgCO2e/kg", "source": "DEFRA", "region": "GLOBAL", "year": 2023},
    {"category": "material", "subcategory": "copper", "factor_value": 2.71,
     "unit": "kgCO2e/kg", "source": "DEFRA", "region": "GLOBAL", "year": 2023},
    {"category": "material", "subcategory": "glass", "factor_value": 0.85,
     "unit": "kgCO2e/kg", "source": "DEFRA", "region": "GLOBAL", "year": 2023},
    {"category": "material", "subcategory": "rubber", "factor_value": 2.85,
     "unit": "kgCO2e/kg", "source": "DEFRA", "region": "GLOBAL", "year": 2023},
    {"category": "material", "subcategory": "cement", "factor_value": 0.93,
     "unit": "kgCO2e/kg", "source": "IPCC", "region": "GLOBAL", "year": 2023},
    {"category": "material", "subcategory": "wood", "factor_value": 0.46,
     "unit": "kgCO2e/kg", "source": "DEFRA", "region": "GLOBAL", "year": 2023},
    {"category": "material", "subcategory": "paper", "factor_value": 0.91,
     "unit": "kgCO2e/kg", "source": "DEFRA", "region": "GLOBAL", "year": 2023},
    {"category": "material", "subcategory": "cardboard", "factor_value": 0.82,
     "unit": "kgCO2e/kg", "source": "DEFRA", "region": "GLOBAL", "year": 2023},

    # Freight (Scope 3 Cat 4 / 9)
    {"category": "freight", "subcategory": "road_hgv", "factor_value": 0.107,
     "unit": "kgCO2e/tonne-km", "source": "DEFRA", "region": "GLOBAL", "year": 2023},
    {"category": "freight", "subcategory": "road_lcv", "factor_value": 0.189,
     "unit": "kgCO2e/tonne-km", "source": "DEFRA", "region": "GLOBAL", "year": 2023},
    {"category": "freight", "subcategory": "rail", "factor_value": 0.028,
     "unit": "kgCO2e/tonne-km", "source": "DEFRA", "region": "GLOBAL", "year": 2023},
    {"category": "freight", "subcategory": "sea_container", "factor_value": 0.016,
     "unit": "kgCO2e/tonne-km", "source": "DEFRA", "region": "GLOBAL", "year": 2023},
    {"category": "freight", "subcategory": "air_freight", "factor_value": 0.602,
     "unit": "kgCO2e/tonne-km", "source": "DEFRA", "region": "GLOBAL", "year": 2023},

    # Business travel (Scope 3 Cat 6)
    {"category": "travel", "subcategory": "flight_domestic", "factor_value": 0.255,
     "unit": "kgCO2e/passenger-km", "source": "DEFRA", "region": "GLOBAL", "year": 2023},
    {"category": "travel", "subcategory": "flight_international", "factor_value": 0.195,
     "unit": "kgCO2e/passenger-km", "source": "DEFRA", "region": "GLOBAL", "year": 2023},
    {"category": "travel", "subcategory": "flight_short_haul", "factor_value": 0.158,
     "unit": "kgCO2e/passenger-km", "source": "DEFRA", "region": "GLOBAL", "year": 2023},
    {"category": "travel", "subcategory": "hotel_night", "factor_value": 20.0,
     "unit": "kgCO2e/night", "source": "DEFRA", "region": "GLOBAL", "year": 2023},
    {"category": "travel", "subcategory": "taxi", "factor_value": 0.148,
     "unit": "kgCO2e/km", "source": "DEFRA", "region": "GLOBAL", "year": 2023},
    {"category": "travel", "subcategory": "train_domestic", "factor_value": 0.041,
     "unit": "kgCO2e/passenger-km", "source": "DEFRA", "region": "IN", "year": 2023},

    # Employee commute (Scope 3 Cat 7)
    {"category": "commute", "subcategory": "car_petrol", "factor_value": 0.17,
     "unit": "kgCO2e/km", "source": "DEFRA", "region": "GLOBAL", "year": 2023},
    {"category": "commute", "subcategory": "car_diesel", "factor_value": 0.164,
     "unit": "kgCO2e/km", "source": "DEFRA", "region": "GLOBAL", "year": 2023},
    {"category": "commute", "subcategory": "two_wheeler", "factor_value": 0.072,
     "unit": "kgCO2e/km", "source": "DEFRA", "region": "IN", "year": 2023},
    {"category": "commute", "subcategory": "bus", "factor_value": 0.089,
     "unit": "kgCO2e/passenger-km", "source": "DEFRA", "region": "GLOBAL", "year": 2023},
    {"category": "commute", "subcategory": "metro_rail", "factor_value": 0.041,
     "unit": "kgCO2e/passenger-km", "source": "DEFRA", "region": "IN", "year": 2023},
    {"category": "commute", "subcategory": "ev_car", "factor_value": 0.053,
     "unit": "kgCO2e/km", "source": "CEA", "region": "IN", "year": 2023},

    # Water
    {"category": "water", "subcategory": "supply", "factor_value": 0.344,
     "unit": "kgCO2e/m3", "source": "DEFRA", "region": "GLOBAL", "year": 2023},
    {"category": "water", "subcategory": "treatment", "factor_value": 0.708,
     "unit": "kgCO2e/m3", "source": "DEFRA", "region": "GLOBAL", "year": 2023},

    # Waste
    {"category": "waste", "subcategory": "landfill_mixed", "factor_value": 0.586,
     "unit": "kgCO2e/kg", "source": "DEFRA", "region": "GLOBAL", "year": 2023},
    {"category": "waste", "subcategory": "recycled_mixed", "factor_value": 0.021,
     "unit": "kgCO2e/kg", "source": "DEFRA", "region": "GLOBAL", "year": 2023},
    {"category": "waste", "subcategory": "composted", "factor_value": 0.010,
     "unit": "kgCO2e/kg", "source": "DEFRA", "region": "GLOBAL", "year": 2023},
    {"category": "waste", "subcategory": "incinerated", "factor_value": 0.213,
     "unit": "kgCO2e/kg", "source": "DEFRA", "region": "GLOBAL", "year": 2023},
]


def seed(db: Session) -> None:
    if db.query(EmissionFactor).count() > 0:
        print("  emission_factors already seeded, skipping")
        return
    db.add_all([EmissionFactor(**f) for f in FACTORS])
    db.flush()
    print(f"  inserted {len(FACTORS)} emission factors")
