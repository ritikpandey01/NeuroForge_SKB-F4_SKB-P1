export type Framework = "BRSR" | "GRI" | "TCFD";
export type ReportStatus = "pending" | "generating" | "ready" | "failed";

export type Report = {
  id: number;
  report_type: string;
  period: string;
  status: ReportStatus;
  file_path: string | null;
  generated_at: string;
};

export type GenerateRequest = {
  framework: Framework;
  period: string;
  include_narrative: boolean;
};

export type NarrativeResponse = {
  narrative: string;
  model: string;
};

export type AnchorManifest = {
  report_root: string;
  activity_root: string;
  factor_root: string;
  evidence_root: string;
  methodology_hash: string;
  pdf_hash: string;
  activity_leaf_count: number;
  factor_leaf_count: number;
  evidence_leaf_count: number;
  period_start: string;
  period_end: string;
};

export type Anchor = {
  id: number;
  report_id: number;
  merkle_root: string;
  chain: string;
  tx_hash: string | null;
  block_number: number | null;
  sealed_by: string;
  sealed_at: string;
};

export type SealResponse = {
  anchor: Anchor;
  manifest: AnchorManifest;
};

export type ChainAnchorResponse = {
  anchor: Anchor;
  explorer_url: string | null;
};

export type VerifyResponse = {
  verified: boolean;
  diverged_subtree: string | null;
  stored_root: string;
  recomputed_root: string;
  stored_manifest: AnchorManifest;
  recomputed_manifest: AnchorManifest;
  sealed_at: string;
  sealed_by: string;
  chain: string;
  tx_hash: string | null;
  block_number: number | null;
};

export const FRAMEWORKS: { value: Framework; label: string; blurb: string }[] = [
  {
    value: "BRSR",
    label: "BRSR",
    blurb: "SEBI Business Responsibility & Sustainability Report — Principle 6 (Environment).",
  },
  {
    value: "GRI",
    label: "GRI 305",
    blurb: "GRI Standards — Emissions 305-1/-2/-3 disclosure.",
  },
  {
    value: "TCFD",
    label: "TCFD",
    blurb: "TCFD Metrics & Targets pillar.",
  },
];
