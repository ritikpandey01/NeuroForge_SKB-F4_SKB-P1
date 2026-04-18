import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, ApiError, tokenStore } from "@/lib/api";

import type {
  Anchor,
  ChainAnchorResponse,
  GenerateRequest,
  NarrativeResponse,
  Report,
  SealResponse,
  VerifyResponse,
} from "./types";

export const useReports = () =>
  useQuery({
    queryKey: ["reports"],
    queryFn: () => api.get<Report[]>("/reports"),
  });

export const useGenerateReport = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: GenerateRequest) => api.post<Report>("/reports/generate", body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["reports"] }),
  });
};

export const useReportNarrative = () =>
  useMutation({
    mutationFn: (id: number) => api.post<NarrativeResponse>(`/reports/${id}/narrative`, {}),
  });

export const downloadUrl = (id: number) => `/api/v1/reports/${id}/download`;

export const assuranceUrl = (id: number) => `/api/v1/reports/${id}/assurance.zip`;

export const useSealReport = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.post<SealResponse>(`/reports/${id}/seal`, {}),
    onSuccess: (_, id) => {
      qc.invalidateQueries({ queryKey: ["reports"] });
      qc.invalidateQueries({ queryKey: ["report-anchor", id] });
    },
  });
};

export const useReportAnchor = (reportId: number) =>
  useQuery({
    queryKey: ["report-anchor", reportId],
    queryFn: async () => {
      try {
        return await api.get<Anchor>(`/reports/${reportId}/anchor`);
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) return null;
        throw err;
      }
    },
  });

export const useVerifyReport = () =>
  useMutation({
    mutationFn: (id: number) => api.get<VerifyResponse>(`/reports/${id}/verify`),
  });

export async function downloadAssuranceBundle(reportId: number): Promise<void> {
  const token = tokenStore.getAccess();
  const res = await fetch(`/api/v1/reports/${reportId}/assurance.zip`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new ApiError(res.status, text || res.statusText);
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  const disp = res.headers.get("Content-Disposition") ?? "";
  const m = /filename="([^"]+)"/.exec(disp);
  a.download = m?.[1] ?? `assurance_${reportId}.zip`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export const useAnchorOnChain = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.post<ChainAnchorResponse>(`/reports/${id}/anchor`, {}),
    onSuccess: (_, id) => {
      qc.invalidateQueries({ queryKey: ["report-anchor", id] });
    },
  });
};
