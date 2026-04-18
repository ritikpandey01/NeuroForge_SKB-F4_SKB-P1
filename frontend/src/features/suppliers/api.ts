import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";

import type {
  ImpactMatrix,
  SubmissionCreate,
  Supplier,
  SupplierCreate,
  SupplierSubmission,
  SupplierUpdate,
} from "./types";

type ListParams = {
  industry?: string;
  tier?: number;
  data_maturity_level?: string;
  search?: string;
};

const qsFrom = (params: Record<string, string | number | undefined>) => {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== "") qs.set(k, String(v));
  }
  const out = qs.toString();
  return out ? `?${out}` : "";
};

export const useSuppliers = (params: ListParams = {}) =>
  useQuery({
    queryKey: ["suppliers", params],
    queryFn: () => api.get<Supplier[]>(`/suppliers${qsFrom(params)}`),
  });

export const useSupplier = (id: number | null) =>
  useQuery({
    queryKey: ["suppliers", id],
    queryFn: () => api.get<Supplier>(`/suppliers/${id}`),
    enabled: id !== null,
  });

export const useImpactMatrix = () =>
  useQuery({
    queryKey: ["suppliers", "impact-matrix"],
    queryFn: () => api.get<ImpactMatrix>("/suppliers/impact-matrix"),
  });

const invalidateSuppliers = (qc: ReturnType<typeof useQueryClient>) => {
  qc.invalidateQueries({ queryKey: ["suppliers"] });
};

export const useCreateSupplier = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: SupplierCreate) =>
      api.post<Supplier>("/suppliers", payload),
    onSuccess: () => invalidateSuppliers(qc),
  });
};

export const useUpdateSupplier = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: SupplierUpdate }) =>
      api.put<Supplier>(`/suppliers/${id}`, payload),
    onSuccess: () => invalidateSuppliers(qc),
  });
};

export const useDeleteSupplier = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.del<unknown>(`/suppliers/${id}`),
    onSuccess: () => invalidateSuppliers(qc),
  });
};

// ── Submissions ───────────────────────────────────────────────────────

export const useSubmissions = (supplierId: number | null) =>
  useQuery({
    queryKey: ["supplier-submissions", supplierId],
    queryFn: () =>
      api.get<SupplierSubmission[]>(`/suppliers/${supplierId}/submissions`),
    enabled: supplierId !== null,
  });

export const useAllSubmissions = (status?: string) =>
  useQuery({
    queryKey: ["supplier-submissions", "all", status ?? ""],
    queryFn: () =>
      api.get<SupplierSubmission[]>(
        `/suppliers/submissions/all${qsFrom({ status })}`,
      ),
  });

export const useCreateSubmission = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      supplierId,
      payload,
    }: {
      supplierId: number;
      payload: SubmissionCreate;
    }) =>
      api.post<SupplierSubmission>(
        `/suppliers/${supplierId}/submissions`,
        payload,
      ),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["supplier-submissions"] });
      qc.invalidateQueries({ queryKey: ["suppliers"] });
    },
  });
};

export const useUpdateSubmissionStatus = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      api.patch<SupplierSubmission>(`/suppliers/submissions/${id}`, {
        status,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["supplier-submissions"] });
      qc.invalidateQueries({ queryKey: ["suppliers"] });
    },
  });
};
