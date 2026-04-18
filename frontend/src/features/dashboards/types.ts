export type ScopeMixItem = {
  scope: number;
  tonnes: number;
  pct: number;
};

export type RiskItem = {
  id: number;
  detector: string;
  severity: string;
  title: string;
  facility_id: number | null;
};

export type ExecutiveDashboard = {
  org_name: string;
  current_year: number;
  prior_year: number;
  current_total_tonnes: number;
  prior_total_tonnes: number;
  yoy_delta_pct: number;
  scope_mix: ScopeMixItem[];
  base_year: number;
  base_year_total_tonnes: number;
  sbti_pathway_target_tonnes: number;
  sbti_gap_tonnes: number;
  net_zero_target_year: number;
  top_risks: RiskItem[];
  reports_generated: number;
  anomalies_open: number;
  anomalies_escalated: number;
  anomalies_board_reviewed: number;
  carbon_price_inr_per_tonne: number;
  carbon_exposure_current_inr: number;
};

export type FacilityTile = {
  facility_id: number;
  name: string;
  location: string;
  total_tonnes: number;
  pct_of_total: number;
  data_quality_pct: number;
  open_anomaly_count: number;
  activity_row_count: number;
};

export type SupplierCompliance = {
  total_suppliers: number;
  current_quarter: string;
  submissions_received: number;
  compliance_pct: number;
};

export type OperationsDashboard = {
  current_year: number;
  activity_rows_this_period: number;
  activity_rows_prior_period: number;
  facilities: FacilityTile[];
  supplier_compliance: SupplierCompliance;
};
