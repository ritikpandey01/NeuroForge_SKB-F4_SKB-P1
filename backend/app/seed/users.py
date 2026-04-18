"""Seed demo users for each organization (admin, analyst, viewer).

Every demo user shares the same password (`carbonlens`) so the login page
can show a short cheatsheet. Passwords are hashed with bcrypt — no clear
text ends up in the DB.
"""

from sqlalchemy.orm import Session

from app.db.models import Organization, User, UserRole
from app.services.auth import hash_password

DEMO_PASSWORD = "carbonlens"

# (email_local, full_name, role)
_USERS_PER_ORG: list[tuple[str, str, UserRole]] = [
    ("admin", "Org Admin", UserRole.admin),
    ("analyst", "ESG Analyst", UserRole.analyst),
    ("viewer", "Board Viewer", UserRole.viewer),
]


def _email_domain_for(org_name: str) -> str:
    if "Greenfield" in org_name:
        return "greenfieldmfg.in"
    if "UltraTech" in org_name:
        return "ultratechcement.com"
    # Fallback: strip non-alphanumerics, lowercase.
    slug = "".join(c.lower() for c in org_name if c.isalnum())
    return f"{slug}.example.com"


def seed_for(db: Session, org: Organization) -> list[User]:
    domain = _email_domain_for(org.name)
    hashed = hash_password(DEMO_PASSWORD)
    created: list[User] = []

    for local, full_name, role in _USERS_PER_ORG:
        email = f"{local}@{domain}"
        existing = db.query(User).filter_by(email=email).first()
        if existing:
            created.append(existing)
            continue

        user = User(
            email=email,
            password_hash=hashed,
            full_name=f"{full_name} — {org.name.split()[0]}",
            role=role.value,
            org_id=org.id,
            is_active=True,
        )
        db.add(user)
        created.append(user)

    db.flush()
    new_count = sum(1 for u in created if u.id is None or u.created_at is None) or len(
        [u for u in created if u in db.new]
    )
    print(f"  {org.name}: ensured {len(created)} users @ {domain}")
    return created


def print_login_cheatsheet(orgs: list[Organization]) -> None:
    print("\n" + "=" * 64)
    print("  Demo logins — shared password: " + DEMO_PASSWORD)
    print("=" * 64)
    for org in orgs:
        domain = _email_domain_for(org.name)
        print(f"  {org.name}")
        for local, _, role in _USERS_PER_ORG:
            print(f"    {role.value:<8}  {local}@{domain}")
    print("=" * 64)
