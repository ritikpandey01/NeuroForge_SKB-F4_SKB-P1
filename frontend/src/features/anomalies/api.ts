import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";

import type {
  Anomaly,
  AnomalyStatus,
  AnomalySummary,
  BoardReviewRequest,
  EscalationRequest,
  ExplainResponse,
  ScanResponse,
} from "./types";

type ListParams = {
  severity?: string;
  status?: string;
  detector?: string;
  facility_id?: number;
  escalation_status?: string;
};

const qs = (params: Record<string, string | number | undefined>) => {
  const s = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== "") s.set(k, String(v));
  }
  const out = s.toString();
  return out ? `?${out}` : "";
};

export const useAnomalies = (params: ListParams = {}) =>
  useQuery({
    queryKey: ["anomalies", params],
    queryFn: () => api.get<Anomaly[]>(`/anomalies${qs(params)}`),
  });

export const useAnomalySummary = () =>
  useQuery({
    queryKey: ["anomalies", "summary"],
    queryFn: () => api.get<AnomalySummary>("/anomalies/summary"),
    refetchInterval: 60_000,
  });

export const useScanAnomalies = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.post<ScanResponse>("/anomalies/scan", {}),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["anomalies"] }),
  });
};

export const useExplainAnomalies = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (limit: number = 20) =>
      api.post<ExplainResponse>(`/anomalies/explain?limit=${limit}`, {}),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["anomalies"] }),
  });
};

export const useUpdateAnomalyStatus = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      status,
      acknowledgedBy,
    }: {
      id: number;
      status: AnomalyStatus;
      acknowledgedBy?: string;
    }) =>
      api.patch<Anomaly>(`/anomalies/${id}`, {
        status,
        acknowledged_by: acknowledgedBy,
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["anomalies"] }),
  });
};

export const useEscalateAnomaly = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: number; body: EscalationRequest }) =>
      api.post<Anomaly>(`/anomalies/${id}/escalate`, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["anomalies"] });
      qc.invalidateQueries({ queryKey: ["dashboards"] });
    },
  });
};

export const useBoardReviewAnomaly = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: number; body: BoardReviewRequest }) =>
      api.post<Anomaly>(`/anomalies/${id}/board-review`, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["anomalies"] });
      qc.invalidateQueries({ queryKey: ["dashboards"] });
    },
  });
};
