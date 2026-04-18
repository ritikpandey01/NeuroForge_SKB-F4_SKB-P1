export type Facility = {
  id: number;
  org_id: number;
  name: string;
  type: string;
  location: string;
  country: string;
  created_at: string;
};

export type ValidationIssue = {
  severity: "error" | "warning" | "info";
  field: string;
  message: string;
};

export type Activity = {
  id: number;
  facility_id: number;
  facility_name: string | null;
  scope: number;
  category: string;
  subcategory: string;
  activity_description: string;
  quantity: number;
  unit: string;
  period_start: string;
  period_end: string;
  source_document: string | null;
  data_quality_score: number;
  verified: boolean;
  uploaded_by: string | null;
  created_at: string;
  updated_at: string;
};

export type ActivityCreate = {
  facility_id: number;
  scope: number;
  category: string;
  subcategory: string;
  activity_description: string;
  quantity: number;
  unit: string;
  period_start: string;
  period_end: string;
  source_document?: string | null;
  data_quality_score?: number;
  uploaded_by?: string | null;
};

export type ActivityWriteResponse = {
  activity: Activity;
  validation: ValidationIssue[];
};

export type CsvPreviewRow = {
  row_number: number;
  raw: Record<string, unknown>;
  parsed: ActivityCreate | null;
  issues: ValidationIssue[];
};

export type CsvPreviewResponse = {
  filename: string;
  summary: {
    total_rows?: number;
    rows_with_errors?: number;
    rows_with_warnings?: number;
    rows_ready?: number;
    error?: string;
    required?: string[];
    optional?: string[];
  };
  rows: CsvPreviewRow[];
  document_summary?: string | null;
  model_warnings?: string[];
};

export type CsvCommitResponse = {
  inserted: number;
  activity_ids: number[];
  calc_errors: { activity_id: number; error: string }[];
};
