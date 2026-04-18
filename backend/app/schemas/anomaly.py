from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

Severity = Literal["critical", "high", "medium", "low"]
DetectorName = Literal["outlier_zscore", "period_gap", "zero_value", "spike_pct"]
AnomalyStatus = Literal["new", "acknowledged", "dismissed", "resolved"]
EscalationStatus = Literal["escalated", "board_reviewed"]


class AnomalyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    detected_at: datetime
    detector: DetectorName
    severity: Severity
    subject_type: str
    subject_id: int | None
    facility_id: int | None
    supplier_id: int | None
    title: str
    description: str
    metric_value: float | None
    expected_value: float | None
    z_score: float | None
    status: AnomalyStatus
    acknowledged_by: str | None
    acknowledged_at: datetime | None
    llm_explanation: str | None
    llm_explained_at: datetime | None
    context: dict[str, Any]

    # Board escalation workflow
    escalation_status: EscalationStatus | None = None
    escalation_owner: str | None = None
    escalation_due_date: date | None = None
    escalation_notes: str | None = None
    escalated_at: datetime | None = None
    board_reviewed_at: datetime | None = None


class AnomalyStatusUpdate(BaseModel):
    status: AnomalyStatus
    acknowledged_by: str | None = None


class EscalationRequest(BaseModel):
    owner: str
    due_date: date | None = None
    notes: str | None = None


class BoardReviewRequest(BaseModel):
    reviewer: str
    notes: str | None = None


class ScanResponse(BaseModel):
    total_detected: int
    new: int
    updated: int
    by_severity: dict[str, int]
    by_detector: dict[str, int]


class ExplainResponse(BaseModel):
    explained: int
    attempted: int
    skipped_reason: str | None = None
