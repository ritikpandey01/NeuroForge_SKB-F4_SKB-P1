from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

Framework = Literal["BRSR", "GRI", "TCFD"]
ReportStatus = Literal["pending", "generating", "ready", "failed"]


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    report_type: str
    period: str
    status: str
    file_path: str | None
    generated_at: datetime


class GenerateReportRequest(BaseModel):
    framework: Framework
    period: str  # e.g. "FY2024" (Apr-Mar) or "2024" (Jan-Dec)
    include_narrative: bool = False


class ReportNarrativeResponse(BaseModel):
    narrative: str
    model: str
