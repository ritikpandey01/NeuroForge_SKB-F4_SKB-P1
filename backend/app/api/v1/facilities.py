from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.db.models import Facility, User, UserRole
from app.db.session import get_db
from app.schemas.facility import FacilityCreate, FacilityOut

router = APIRouter(prefix="/facilities")


@router.get("", response_model=list[FacilityOut])
def list_facilities(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Facility]:
    return list(
        db.scalars(
            select(Facility).where(Facility.org_id == user.org_id).order_by(Facility.name)
        ).all()
    )


@router.post(
    "",
    response_model=FacilityOut,
    status_code=status.HTTP_201_CREATED,
)
def create_facility(
    body: FacilityCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin, UserRole.analyst)),
) -> Facility:
    existing = db.scalar(
        select(Facility).where(
            Facility.org_id == user.org_id, Facility.name == body.name
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A facility named '{body.name}' already exists.",
        )
    facility = Facility(
        org_id=user.org_id,
        name=body.name,
        type=body.type,
        location=body.location,
        country=body.country,
        default_department_head_name=body.default_department_head_name,
        default_department_head_email=(
            str(body.default_department_head_email)
            if body.default_department_head_email
            else None
        ),
    )
    db.add(facility)
    db.commit()
    db.refresh(facility)
    return facility
