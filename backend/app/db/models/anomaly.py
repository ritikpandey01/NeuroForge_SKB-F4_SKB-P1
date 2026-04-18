from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AnomalyDetection(Base):
    """A flagged irregularity from the statistical sweep. Persisted so the UI
    can show a stable feed across sessions and the ack/dismiss workflow can
    track who acted on what.

    `subject_type` + `subject_id` is a deliberate loose FK — the detector
    produces anomalies tied to different tables (activity_data, emission,
    supplier_submission, or nothing at all for "missing period" gaps).
    Hard FKs would force nullable columns per table and cascade logic we
    don't need; a polymorphic pair keeps it simple.
    """

    __tablename__ = "anomaly_detections"

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True
    )
    detected_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    detector: Mapped[str] = mapped_column(String(40), index=True)
    # "outlier_zscore" | "period_gap" | "zero_value" | "spike_pct"

    severity: Mapped[str] = mapped_column(String(20), index=True)
    # "critical" | "high" | "medium" | "low"

    subject_type: Mapped[str] = mapped_column(String(40), index=True)
    # "activity_data" | "supplier_submission" | "facility_gap"
    subject_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    facility_id: Mapped[int | None] = mapped_column(
        ForeignKey("facilities.id", ondelete="SET NULL"), nullable=True, index=True
    )
    supplier_id: Mapped[int | None] = mapped_column(
        ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True, index=True
    )

    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)

    metric_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    expected_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    z_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Deterministic dedupe key — the detector reuses this on re-runs so a single
    # underlying issue never balloons into N rows.
    fingerprint: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    status: Mapped[str] = mapped_column(String(20), default="new", index=True)
    # "new" | "acknowledged" | "dismissed" | "resolved"

    acknowledged_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # LLM-generated plain-English explanation. Nullable because the LLM may be
    # unavailable (no key / circuit open) — detection itself never depends on it.
    llm_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    llm_explained_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Free-form detector-specific context (trailing stats, period, etc.)
    context: Mapped[dict] = mapped_column(JSON, default=dict)

    # Board escalation workflow (PS: "formal escalation mechanisms for board oversight").
    # Independent of the ack/dismiss workflow — an item can be acknowledged by ops AND
    # escalated to board simultaneously.
    escalation_status: Mapped[str | None] = mapped_column(
        String(30), nullable=True, index=True
    )
    # None | "escalated" | "board_reviewed"
    escalation_owner: Mapped[str | None] = mapped_column(String(100), nullable=True)
    escalation_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    escalation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    escalated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    board_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
