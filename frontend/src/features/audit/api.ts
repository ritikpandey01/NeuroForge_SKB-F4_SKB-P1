import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";

import type { AuditFilterOptions, AuditFilters, AuditPage } from "./types";

function toQueryString(f: AuditFilters): string {
  const p = new URLSearchParams();
  p.set("limit", String(f.limit));
  p.set("offset", String(f.offset));
  if (f.entity_type) p.set("entity_type", f.entity_type);
  if (f.action) p.set("action", f.action);
  if (f.user) p.set("user", f.user);
  if (f.from) p.set("from", f.from);
  if (f.to) p.set("to", f.to);
  if (f.q) p.set("q", f.q);
  return p.toString();
}

export const useAuditLog = (filters: AuditFilters) =>
  useQuery({
    queryKey: ["audit-log", filters],
    queryFn: () => api.get<AuditPage>(`/audit-log?${toQueryString(filters)}`),
    placeholderData: (prev) => prev,
  });

export const useAuditFilterOptions = () =>
  useQuery({
    queryKey: ["audit-log", "filter-options"],
    queryFn: () => api.get<AuditFilterOptions>("/audit-log/filter-options"),
    staleTime: 60_000,
  });
