export type LeverName =
  | "renewable_electricity_share"
  | "energy_efficiency_pct"
  | "fleet_electrification"
  | "supplier_engagement"
  | "logistics_mode_shift";

export type Levers = Record<LeverName, number>;

export type PresetName = "net_zero_2050" | "sbti_1p5" | "business_as_usual";

export type YearPoint = {
  year: number;
  scope_1: number;
  scope_2: number;
  scope_3: number;
  total: number;
};

export type LeverContribution = {
  lever: LeverName;
  avoided_tonnes: number;
  pct_of_baseline: number;
};

export type ExposurePoint = {
  year: number;
  baseline_inr: number;
  scenario_inr: number;
  savings_inr: number;
};

export type ScenarioResponse = {
  baseline_year: number;
  target_year: number;
  baseline_total_tonnes: number;
  baseline_scope_1: number;
  baseline_scope_2: number;
  baseline_scope_3: number;
  baseline: YearPoint[];
  scenario: YearPoint[];
  sbti: YearPoint[];
  lever_contributions: LeverContribution[];
  scope_deltas_pct: Record<string, number>;
  levers_applied: Record<string, number>;
  carbon_price_inr_per_tonne: number;
  exposure_by_year: ExposurePoint[];
  baseline_total_exposure_inr: number;
  scenario_total_exposure_inr: number;
  total_savings_inr: number;
};

export type ScenarioRequest = {
  baseline_year?: number;
  target_year: number;
  levers: Levers;
  preset?: PresetName;
  carbon_price_inr_per_tonne?: number;
};

export type NarrativeResponse = {
  narrative: string;
  model: string;
};

export const ZERO_LEVERS: Levers = {
  renewable_electricity_share: 0,
  energy_efficiency_pct: 0,
  fleet_electrification: 0,
  supplier_engagement: 0,
  logistics_mode_shift: 0,
};

export const LEVER_LABELS: Record<LeverName, { title: string; affects: string; tooltip: string }> = {
  renewable_electricity_share: {
    title: "Renewable electricity share",
    affects: "Scope 2",
    tooltip: "At 100%, removes up to 95% of Scope 2 electricity emissions.",
  },
  energy_efficiency_pct: {
    title: "Energy efficiency",
    affects: "Scope 1 + Scope 2",
    tooltip: "At 100%, cuts 30% of both Scope 1 fuel use and Scope 2 electricity.",
  },
  fleet_electrification: {
    title: "Fleet electrification",
    affects: "Scope 1",
    tooltip: "At 100%, removes up to 50% of Scope 1 — the mobile-combustion share.",
  },
  supplier_engagement: {
    title: "Supplier engagement",
    affects: "Scope 3 Cat 1",
    tooltip:
      "At 100%, removes up to 40% of Scope 3 via supplier-specific factors replacing spend-based defaults.",
  },
  logistics_mode_shift: {
    title: "Logistics mode shift",
    affects: "Scope 3 Cat 4",
    tooltip: "At 100%, removes up to 30% of Scope 3 via road → rail transport substitution.",
  },
};
