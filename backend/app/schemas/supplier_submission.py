from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

SubmissionStatus = Literal["pending", "accepted", "flagged", "rejected"]


class SubmissionBase(BaseModel):
    period: str = Field(min_length=4, max_length=20)  # e.g. "2024-Q3", "2024-07"
    submitted_data: dict[str, Any]
    data_quality_score: int = Field(default=3, ge=1, le=5)


class SubmissionCreate(SubmissionBase):
    pass


class SubmissionStatusUpdate(BaseModel):
    status: SubmissionStatus


class SubmissionOut(SubmissionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    supplier_id: int
    status: SubmissionStatus
    submitted_at: datetime
    reviewed_at: datetime | None = None
    supplier_name: str | None = None
