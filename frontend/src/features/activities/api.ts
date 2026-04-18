import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";

import type {
  Activity,
  ActivityCreate,
  ActivityWriteResponse,
  CsvCommitResponse,
  CsvPreviewResponse,
  Facility,
} from "./types";

export const useFacilities = () =>
  useQuery({
    queryKey: ["facilities"],
    queryFn: () => api.get<Facility[]>("/facilities"),
    staleTime: 5 * 60_000,
  });

type ListParams = {
  facility_id?: number;
  scope?: number;
  limit?: number;
};

export const useActivities = (params: ListParams = {}) =>
  useQuery({
    queryKey: ["activities", params],
    queryFn: () => {
      const qs = new URLSearchParams();
      if (params.facility_id) qs.set("facility_id", String(params.facility_id));
      if (params.scope) qs.set("scope", String(params.scope));
      if (params.limit) qs.set("limit", String(params.limit));
      const q = qs.toString();
      return api.get<Activity[]>(`/activities${q ? `?${q}` : ""}`);
    },
  });

const invalidateAll = (qc: ReturnType<typeof useQueryClient>) => {
  qc.invalidateQueries({ queryKey: ["activities"] });
  qc.invalidateQueries({ queryKey: ["emissions"] });
};

export const useCreateActivity = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: ActivityCreate) =>
      api.post<ActivityWriteResponse>("/activities", payload),
    onSuccess: () => invalidateAll(qc),
  });
};

export const useDeleteActivity = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.del<unknown>(`/activities/${id}`),
    onSuccess: () => invalidateAll(qc),
  });
};

const multipartPreview = async (
  url: string,
  file: File,
  extra: Record<string, string | undefined> = {},
): Promise<CsvPreviewResponse> => {
  const fd = new FormData();
  fd.append("file", file);
  for (const [k, v] of Object.entries(extra)) {
    if (v) fd.append(k, v);
  }
  const res = await fetch(url, { method: "POST", body: fd });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(text || res.statusText);
  }
  return (await res.json()) as CsvPreviewResponse;
};

export const useCsvPreview = () =>
  useMutation({
    mutationFn: ({ file, uploadedBy }: { file: File; uploadedBy?: string }) =>
      multipartPreview("/api/v1/uploads/csv/preview", file, {
        uploaded_by: uploadedBy,
      }),
  });

export const useDocumentPreview = () =>
  useMutation({
    mutationFn: ({
      file,
      uploadedBy,
      docType,
    }: {
      file: File;
      uploadedBy?: string;
      docType?: string;
    }) =>
      multipartPreview("/api/v1/uploads/document/preview", file, {
        uploaded_by: uploadedBy,
        doc_type: docType,
      }),
  });

export type DocumentTypeOption = { key: string; hint: string };

export const useDocumentTypes = () =>
  useQuery({
    queryKey: ["document-types"],
    queryFn: () =>
      api.get<{ types: DocumentTypeOption[] }>("/uploads/document/types"),
    staleTime: 60 * 60_000,
  });

export const useCsvCommit = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (rows: ActivityCreate[]) =>
      api.post<CsvCommitResponse>("/uploads/csv/commit", { rows }),
    onSuccess: () => invalidateAll(qc),
  });
};
