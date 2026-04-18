export type ScopeBreakdown = {
  scope: number;
  co2e_tonnes: number;
  pct_of_total: number;
};

export type CategoryBreakdown = {
  category: string;
  scope: number;
  co2e_tonnes: number;
};

export type FacilityBreakdown = {
  facility_id: number;
  facility_name: string;
  co2e_tonnes: number;
};

export type MonthlyPoint = {
  period: string;
  scope_1: number;
  scope_2: number;
  scope_3: number;
  total: number;
};

export type EmissionsSummary = {
  period_start: string | null;
  period_end: string | null;
  total_co2e_tonnes: number;
  by_scope: ScopeBreakdown[];
  by_category: CategoryBreakdown[];
  by_facility: FacilityBreakdown[];
  monthly: MonthlyPoint[];
  data_quality_verified_pct: number;
};

export type EmissionFactor = {
  id: number;
  category: string;
  subcategory: string;
  factor_value: number;
  unit: string;
  source: string;
  region: string;
  year: number;
};

export type EmissionLedgerRow = {
  id: number;
  activity_id: number;
  facility_id: number;
  facility_name: string;
  scope: number;
  category: string;
  subcategory: string;
  quantity: number;
  unit: string;
  period_start: string;
  period_end: string;
  co2e_kg: number;
  co2e_tonnes: number;
  calculation_method: string;
  factor_source: string | null;
  data_quality_score: number;
  verified: boolean;
};

export type Methodology = {
  emission_id: number;
  activity_id: number;
  scope: number;
  category: string;
  subcategory: string;
  activity_description: string;
  quantity: number;
  unit: string;
  period_start: string;
  period_end: string;
  factor_id: number | null;
  factor_value: number | null;
  factor_unit: string | null;
  factor_source: string | null;
  factor_year: number | null;
  co2e_kg: number;
  co2e_tonnes: number;
  calculation_method: string;
  data_quality_score: number;
  verified: boolean;
};
