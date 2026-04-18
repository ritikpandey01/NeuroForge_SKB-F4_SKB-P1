from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class FacilityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    org_id: int
    name: str
    type: str
    location: str
    country: str
    default_department_head_name: str | None = None
    default_department_head_email: str | None = None
    created_at: datetime


class FacilityCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    type: str = Field(min_length=1, max_length=50)
    location: str = Field(min_length=1, max_length=200)
    country: str = Field(min_length=1, max_length=100)
    default_department_head_name: str | None = Field(default=None, max_length=200)
    default_department_head_email: EmailStr | None = None
