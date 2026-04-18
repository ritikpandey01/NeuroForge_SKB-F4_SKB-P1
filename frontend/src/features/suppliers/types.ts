export type MaturityLevel =
  | "spend_based"
  | "activity_based"
  | "verified_primary";

export type SpendBucket = "low" | "medium" | "high";

export type SubmissionStatus =
  | "pending"
  | "accepted"
  | "flagged"
  | "rejected";

export type Supplier = {
  id: number;
  org_id: number;
  name: string;
  industry: string;
  country: string;
  contact_email: string | null;
  tier: number;
  data_maturity_level: MaturityLevel;
  scope3_category: string;
  annual_spend: number;
  created_at: string;
  submissions_count: number;
  latest_submission_status: SubmissionStatus | null;
};

export type SupplierCreate = {
  name: string;
  industry: string;
  country: string;
  contact_email?: string | null;
  tier: number;
  data_maturity_level: MaturityLevel;
  scope3_category: string;
  annual_spend: number;
};

export type SupplierUpdate = Partial<SupplierCreate>;

export type MatrixCell = {
  spend_bucket: SpendBucket;
  data_maturity_level: MaturityLevel;
  supplier_count: number;
  total_spend: number;
  supplier_ids: number[];
};

export type ImpactMatrix = {
  spend_thresholds: { low_max: number; medium_max: number };
  cells: MatrixCell[];
  total_suppliers: number;
  total_spend: number;
};

export type SupplierSubmission = {
  id: number;
  supplier_id: number;
  supplier_name: string | null;
  period: string;
  submitted_data: Record<string, unknown>;
  data_quality_score: number;
  status: SubmissionStatus;
  submitted_at: string;
  reviewed_at: string | null;
};

export type SubmissionCreate = {
  period: string;
  submitted_data: Record<string, unknown>;
  data_quality_score?: number;
};
