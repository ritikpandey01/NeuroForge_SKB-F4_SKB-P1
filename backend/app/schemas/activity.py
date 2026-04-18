from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ActivityBase(BaseModel):
    facility_id: int
    scope: int = Field(ge=1, le=3)
    category: str
    subcategory: str
    activity_description: str
    quantity: float = Field(ge=0)
    unit: str
    period_start: date
    period_end: date
    source_document: str | None = None
    data_quality_score: int = Field(default=3, ge=1, le=5)
    verified: bool = False
    uploaded_by: str | None = None


class ActivityCreate(ActivityBase):
    pass


class ActivityUpdate(BaseModel):
    facility_id: int | None = None
    scope: int | None = Field(default=None, ge=1, le=3)
    category: str | None = None
    subcategory: str | None = None
    activity_description: str | None = None
    quantity: float | None = Field(default=None, ge=0)
    unit: str | None = None
    period_start: date | None = None
    period_end: date | None = None
    source_document: str | None = None
    data_quality_score: int | None = Field(default=None, ge=1, le=5)
    verified: bool | None = None


class ValidationIssueOut(BaseModel):
    severity: str
    field: str
    message: str


class ActivityOut(ActivityBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    facility_name: str | None = None
    created_at: datetime
    updated_at: datetime


class ActivityWriteResponse(BaseModel):
    activity: ActivityOut
    validation: list[ValidationIssueOut] = []