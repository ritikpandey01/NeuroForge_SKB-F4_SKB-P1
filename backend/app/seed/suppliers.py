"""Seed 15 suppliers across 4 Scope 3 categories with varying maturity."""

from sqlalchemy.orm import Session

from app.db.models import Organization, Supplier

SUPPLIERS: list[dict] = [
    {"name": "SteelCorp India", "industry": "Steel", "tier": 1,
     "data_maturity_level": "activity_based", "scope3_category": "Cat1_PurchasedGoods_Steel",
     "annual_spend": 45.0},
    {"name": "MetalWorks Ltd", "industry": "Aluminium", "tier": 1,
     "data_maturity_level": "spend_based", "scope3_category": "Cat1_PurchasedGoods_Aluminium",
     "annual_spend": 12.0},
    {"name": "PolyPack Solutions", "industry": "Plastics", "tier": 2,
     "data_maturity_level": "spend_based", "scope3_category": "Cat1_PurchasedGoods_Plastics",
     "annual_spend": 8.0},
    {"name": "FastFreight Logistics", "industry": "Logistics", "tier": 1,
     "data_maturity_level": "activity_based", "scope3_category": "Cat4_UpstreamTransport",
     "annual_spend": 15.0},
    {"name": "RoadHaul Express", "industry": "Logistics", "tier": 2,
     "data_maturity_level": "spend_based", "scope3_category": "Cat4_UpstreamTransport",
     "annual_spend": 6.0},
    {"name": "Precision Parts Co", "industry": "Components", "tier": 1,
     "data_maturity_level": "verified_primary", "scope3_category": "Cat1_PurchasedGoods_Components",
     "annual_spend": 22.0},
    {"name": "CopperLine Industries", "industry": "Components", "tier": 1,
     "data_maturity_level": "activity_based", "scope3_category": "Cat1_PurchasedGoods_Components",
     "annual_spend": 18.0},
    {"name": "GlassCraft India", "industry": "Components", "tier": 2,
     "data_maturity_level": "spend_based", "scope3_category": "Cat1_PurchasedGoods_Components",
     "annual_spend": 5.0},
    {"name": "RubberTech Solutions", "industry": "Components", "tier": 2,
     "data_maturity_level": "spend_based", "scope3_category": "Cat1_PurchasedGoods_Components",
     "annual_spend": 4.0},
    {"name": "QuickShip Cargo", "industry": "Logistics", "tier": 1,
     "data_maturity_level": "activity_based", "scope3_category": "Cat4_UpstreamTransport",
     "annual_spend": 9.0},
    {"name": "MumbaiLogix", "industry": "Logistics", "tier": 3,
     "data_maturity_level": "spend_based", "scope3_category": "Cat4_UpstreamTransport",
     "annual_spend": 3.0},
    {"name": "TechBearings Ltd", "industry": "Components", "tier": 1,
     "data_maturity_level": "verified_primary", "scope3_category": "Cat1_PurchasedGoods_Components",
     "annual_spend": 14.0},
    {"name": "CastingWorks Pvt", "industry": "Components", "tier": 1,
     "data_maturity_level": "activity_based", "scope3_category": "Cat1_PurchasedGoods_Components",
     "annual_spend": 11.0},
    {"name": "PackPro Industries", "industry": "Packaging", "tier": 2,
     "data_maturity_level": "spend_based", "scope3_category": "Cat1_PurchasedGoods_Packaging",
     "annual_spend": 7.0},
    {"name": "ChemFlex Corp", "industry": "Chemicals", "tier": 2,
     "data_maturity_level": "spend_based", "scope3_category": "Cat1_PurchasedGoods_Chemicals",
     "annual_spend": 10.0},
]


# UltraTech's real supplier universe is huge; this is a representative slice
# of their top categories (limestone, gypsum, fly-ash, pet-coke, freight).
ULTRATECH_SUPPLIERS: list[dict] = [
    {"name": "Reliance Petcoke", "industry": "Pet-coke",
     "tier": 1, "data_maturity_level": "activity_based",
     "scope3_category": "Cat1_PurchasedGoods_Fuel", "annual_spend": 380.0},
    {"name": "Indian Oil Bulk Fuels", "industry": "Pet-coke",
     "tier": 1, "data_maturity_level": "spend_based",
     "scope3_category": "Cat1_PurchasedGoods_Fuel", "annual_spend": 210.0},
    {"name": "South Eastern Coalfields", "industry": "Coal",
     "tier": 1, "data_maturity_level": "activity_based",
     "scope3_category": "Cat1_PurchasedGoods_Fuel", "annual_spend": 165.0},
    {"name": "Gujarat Mineral Development", "industry": "Limestone",
     "tier": 1, "data_maturity_level": "verified_primary",
     "scope3_category": "Cat1_PurchasedGoods_Material", "annual_spend": 95.0},
    {"name": "Rajasthan Gypsum Co", "industry": "Gypsum",
     "tier": 1, "data_maturity_level": "spend_based",
     "scope3_category": "Cat1_PurchasedGoods_Material", "annual_spend": 42.0},
    {"name": "NTPC Ash Utilization", "industry": "Fly-ash",
     "tier": 1, "data_maturity_level": "activity_based",
     "scope3_category": "Cat1_PurchasedGoods_Material", "annual_spend": 38.0},
    {"name": "JSW Slag Supplies", "industry": "Slag",
     "tier": 1, "data_maturity_level": "activity_based",
     "scope3_category": "Cat1_PurchasedGoods_Material", "annual_spend": 34.0},
    {"name": "CONCOR Rail Logistics", "industry": "Logistics",
     "tier": 1, "data_maturity_level": "verified_primary",
     "scope3_category": "Cat4_UpstreamTransport", "annual_spend": 220.0},
    {"name": "TCI Freight Services", "industry": "Logistics",
     "tier": 1, "data_maturity_level": "activity_based",
     "scope3_category": "Cat4_UpstreamTransport", "annual_spend": 155.0},
    {"name": "Adani Logistics Bulk", "industry": "Logistics",
     "tier": 1, "data_maturity_level": "activity_based",
     "scope3_category": "Cat4_UpstreamTransport", "annual_spend": 120.0},
    {"name": "Delhivery Road Haul", "industry": "Logistics",
     "tier": 2, "data_maturity_level": "spend_based",
     "scope3_category": "Cat4_UpstreamTransport", "annual_spend": 48.0},
    {"name": "RefractoryLine India", "industry": "Refractories",
     "tier": 2, "data_maturity_level": "spend_based",
     "scope3_category": "Cat1_PurchasedGoods_Components", "annual_spend": 28.0},
    {"name": "Grinding Media Forge", "industry": "Steel",
     "tier": 2, "data_maturity_level": "spend_based",
     "scope3_category": "Cat1_PurchasedGoods_Components", "annual_spend": 22.0},
    {"name": "PackJute Industries", "industry": "Packaging",
     "tier": 2, "data_maturity_level": "spend_based",
     "scope3_category": "Cat1_PurchasedGoods_Packaging", "annual_spend": 18.0},
    {"name": "BulkChem Additives", "industry": "Chemicals",
     "tier": 3, "data_maturity_level": "spend_based",
     "scope3_category": "Cat1_PurchasedGoods_Chemicals", "annual_spend": 8.0},
]


def seed(db: Session, org: Organization) -> None:
    _seed_list(db, org, SUPPLIERS, label="Greenfield")


def seed_ultratech(db: Session, org: Organization) -> None:
    _seed_list(db, org, ULTRATECH_SUPPLIERS, label="UltraTech")


def _seed_list(
    db: Session, org: Organization, rows: list[dict], *, label: str
) -> None:
    if db.query(Supplier).filter_by(org_id=org.id).count() > 0:
        print(f"  {label} suppliers already seeded, skipping")
        return
    for s in rows:
        db.add(
            Supplier(
                org_id=org.id,
                country="India",
                contact_email=f"esg@{s['name'].lower().replace(' ', '')}.example.com",
                **s,
            )
        )
    db.flush()
    print(f"  {label}: inserted {len(rows)} suppliers")
