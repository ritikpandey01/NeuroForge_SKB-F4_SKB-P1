from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import EmissionFactor, User
from app.db.session import get_db
from app.schemas.factor import EmissionFactorOut

router = APIRouter(prefix="/emission-factors")


@router.get("", response_model=list[EmissionFactorOut])
def list_factors(
    category: str | None = Query(None),
    region: str | None = Query(None),
    year: int | None = Query(None),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[EmissionFactor]:
    stmt = select(EmissionFactor).order_by(
        EmissionFactor.category, EmissionFactor.subcategory
    )
    if category:
        stmt = stmt.where(EmissionFactor.category == category)
    if region:
        stmt = stmt.where(EmissionFactor.region == region)
    if year:
        stmt = stmt.where(EmissionFactor.year == year)
    return list(db.scalars(stmt).all())
