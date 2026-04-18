import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";

import type { ExecutiveDashboard, OperationsDashboard } from "./types";

export const useExecutiveDashboard = () =>
  useQuery({
    queryKey: ["dashboards", "executive"],
    queryFn: () => api.get<ExecutiveDashboard>("/dashboards/executive"),
  });

export const useOperationsDashboard = () =>
  useQuery({
    queryKey: ["dashboards", "operations"],
    queryFn: () => api.get<OperationsDashboard>("/dashboards/operations"),
  });
