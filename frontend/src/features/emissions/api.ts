import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";

import type {
  EmissionFactor,
  EmissionLedgerRow,
  EmissionsSummary,
  Methodology,
} from "./types";

type SummaryParams = {
  facility_id?: number;
  period_start?: string;
  period_end?: string;
};

type LedgerParams = SummaryParams & {
  scope?: number;
  limit?: number;
};

const buildQuery = (params: Record<string, string | number | undefined>) => {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== "" && v !== null) qs.set(k, String(v));
  }
  const q = qs.toString();
  return q ? `?${q}` : "";
};

export const useEmissionsSummary = (params: SummaryParams = {}) =>
  useQuery({
    queryKey: ["emissions", "summary", params],
    queryFn: () => api.get<EmissionsSummary>(`/emissions/summary${buildQuery(params)}`),
  });

export const useEmissionsList = (params: LedgerParams = {}) =>
  useQuery({
    queryKey: ["emissions", "ledger", params],
    queryFn: () => api.get<EmissionLedgerRow[]>(`/emissions${buildQuery(params)}`),
  });

export const useEmissionMethodology = (id: number | null) =>
  useQuery({
    queryKey: ["emissions", "methodology", id],
    enabled: id != null,
    queryFn: () => api.get<Methodology>(`/emissions/${id}/methodology`),
  });

export const useEmissionFactors = () =>
  useQuery({
    queryKey: ["emission-factors"],
    queryFn: () => api.get<EmissionFactor[]>("/emission-factors"),
  });
