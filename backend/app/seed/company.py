"""Seed Greenfield Manufacturing (demo) and UltraTech Cement (real-data org)."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models import Facility, Organization

ORG_NAME = "Greenfield Manufacturing Pvt. Ltd."

FACILITIES: list[dict] = [
    {
        "name": "Pune Factory", "type": "factory",
        "location": "Chakan, Pune", "country": "India",
        "default_department_head_name": "Anjali Deshpande",
        "default_department_head_email": "anjali.deshpande@greenfieldmfg.in",
    },
    {
        "name": "Chennai Factory", "type": "factory",
        "location": "Sriperumbudur, Chennai", "country": "India",
        "default_department_head_name": "Rajesh Iyer",
        "default_department_head_email": "rajesh.iyer@greenfieldmfg.in",
    },
    {
        "name": "Mumbai Corporate Office", "type": "office",
        "location": "Bandra-Kurla, Mumbai", "country": "India",
        "default_department_head_name": "Priya Nair",
        "default_department_head_email": "priya.nair@greenfieldmfg.in",
    },
]


ULTRATECH_NAME = "UltraTech Cement Limited"

# Ten real UltraTech plants with approximate FY24 production weights.
# Weights sum to 1.0; absolute tonnage is applied at activity-seed time so the
# overall portfolio totals ~118 Mt cementitious for FY24 (matches the
# published ESG Factbook production figure).
ULTRATECH_FACILITIES: list[dict] = [
    {"name": "Rawan Cement Works", "type": "integrated_plant",
     "location": "Rawan, Chhattisgarh", "country": "India", "weight": 0.12,
     "default_department_head_name": "Suresh Kumar",
     "default_department_head_email": "head.rawan@ultratechcement.com"},
    {"name": "Awarpur Cement Works", "type": "integrated_plant",
     "location": "Awarpur, Maharashtra", "country": "India", "weight": 0.12,
     "default_department_head_name": "Vikram Patil",
     "default_department_head_email": "head.awarpur@ultratechcement.com"},
    {"name": "Kovaya Cement Works", "type": "integrated_plant",
     "location": "Kovaya, Gujarat", "country": "India", "weight": 0.12,
     "default_department_head_name": "Harshad Mehta",
     "default_department_head_email": "head.kovaya@ultratechcement.com"},
    {"name": "Hirmi Cement Works", "type": "integrated_plant",
     "location": "Hirmi, Chhattisgarh", "country": "India", "weight": 0.10,
     "default_department_head_name": "Amit Shukla",
     "default_department_head_email": "head.hirmi@ultratechcement.com"},
    {"name": "Jafrabad Cement Works", "type": "integrated_plant",
     "location": "Jafrabad, Gujarat", "country": "India", "weight": 0.11,
     "default_department_head_name": "Nitin Desai",
     "default_department_head_email": "head.jafrabad@ultratechcement.com"},
    {"name": "Reddipalayam Cement Works", "type": "integrated_plant",
     "location": "Ariyalur, Tamil Nadu", "country": "India", "weight": 0.10,
     "default_department_head_name": "Karthik Subramanian",
     "default_department_head_email": "head.reddipalayam@ultratechcement.com"},
    {"name": "Ginigera Cement Works", "type": "integrated_plant",
     "location": "Ginigera, Karnataka", "country": "India", "weight": 0.11,
     "default_department_head_name": "Ravi Gowda",
     "default_department_head_email": "head.ginigera@ultratechcement.com"},
    {"name": "Dhar Cement Works", "type": "grinding_unit",
     "location": "Dhar, Madhya Pradesh", "country": "India", "weight": 0.07,
     "default_department_head_name": "Manoj Tiwari",
     "default_department_head_email": "head.dhar@ultratechcement.com"},
    {"name": "Hotgi Grinding Unit", "type": "grinding_unit",
     "location": "Hotgi, Maharashtra", "country": "India", "weight": 0.07,
     "default_department_head_name": "Prakash Jadhav",
     "default_department_head_email": "head.hotgi@ultratechcement.com"},
    {"name": "Magdalla Grinding Unit", "type": "grinding_unit",
     "location": "Magdalla, Gujarat", "country": "India", "weight": 0.08,
     "default_department_head_name": "Jignesh Shah",
     "default_department_head_email": "head.magdalla@ultratechcement.com"},
    {"name": "Mumbai Corporate HQ", "type": "office",
     "location": "Worli, Mumbai", "country": "India", "weight": 0.00,
     "default_department_head_name": "Meera Krishnan",
     "default_department_head_email": "head.hq@ultratechcement.com"},
]


def seed(db: Session) -> Organization:
    existing = db.query(Organization).filter_by(name=ORG_NAME).first()
    if existing:
        print(f"  organization '{ORG_NAME}' already seeded, skipping")
        return existing

    org = Organization(
        name=ORG_NAME,
        industry="Auto Components Manufacturing",
        country="India",
        base_year=2022,
        net_zero_target_year=2045,
        onboarding_completed_at=datetime.utcnow(),
    )
    db.add(org)
    db.flush()

    for f in FACILITIES:
        db.add(Facility(org_id=org.id, **f))
    db.flush()

    print(f"  inserted organization + {len(FACILITIES)} facilities")
    return org


def seed_ultratech(db: Session) -> Organization:
    existing = db.query(Organization).filter_by(name=ULTRATECH_NAME).first()
    if existing:
        print(f"  organization '{ULTRATECH_NAME}' already seeded, skipping")
        return existing

    # Base year 2017 matches UltraTech's SBTi-aligned commitment (27% intensity
    # reduction by 2032 vs FY17). Net-zero 2050 per their public roadmap.
    # Carbon price ₹2000/t is conservative — internal shadow prices at Indian
    # cement majors are typically quoted in the ₹1500–₹2500 range.
    org = Organization(
        name=ULTRATECH_NAME,
        industry="Cement Manufacturing",
        country="India",
        base_year=2017,
        net_zero_target_year=2050,
        carbon_price_inr_per_tonne=2000.0,
        onboarding_completed_at=datetime.utcnow(),
    )
    db.add(org)
    db.flush()

    for f in ULTRATECH_FACILITIES:
        data = {k: v for k, v in f.items() if k != "weight"}
        db.add(Facility(org_id=org.id, **data))
    db.flush()

    print(f"  inserted organization + {len(ULTRATECH_FACILITIES)} facilities")
    return org
