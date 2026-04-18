export type Severity = "critical" | "high" | "medium" | "low";
export type Detector = "outlier_zscore" | "period_gap" | "zero_value" | "spike_pct";
export type AnomalyStatus = "new" | "acknowledged" | "dismissed" | "resolved";
export type EscalationStatus = "escalated" | "board_reviewed";

export type Anomaly = {
  id: number;
  detected_at: string;
  detector: Detector;
  severity: Severity;
  subject_type: string;
  subject_id: number | null;
  facility_id: number | null;
  supplier_id: number | null;
  title: string;
  description: string;
  metric_value: number | null;
  expected_value: number | null;
  z_score: number | null;
  status: AnomalyStatus;
  acknowledged_by: string | null;
  acknowledged_at: string | null;
  llm_explanation: string | null;
  llm_explained_at: string | null;
  context: Record<string, unknown>;
  escalation_status: EscalationStatus | null;
  escalation_owner: string | null;
  escalation_due_date: string | null;
  escalation_notes: string | null;
  escalated_at: string | null;
  board_reviewed_at: string | null;
};

export type AnomalySummary = {
  by_severity: Partial<Record<Severity, number>>;
  by_status: Partial<Record<AnomalyStatus, number>>;
  open_count: number;
  escalated_count: number;
  board_reviewed_count: number;
};

export type EscalationRequest = {
  owner: string;
  due_date?: string | null;
  notes?: string | null;
};

export type BoardReviewRequest = {
  reviewer: string;
  notes?: string | null;
};

export type ScanResponse = {
  total_detected: number;
  new: number;
  updated: number;
  by_severity: Record<string, number>;
  by_detector: Record<string, number>;
};

export type ExplainResponse = {
  explained: number;
  attempted: number;
  skipped_reason: string | null;
};
