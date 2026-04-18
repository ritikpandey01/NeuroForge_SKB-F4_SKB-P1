import { useMutation } from "@tanstack/react-query";

import { api } from "@/lib/api";

import type {
  NarrativeResponse,
  ScenarioRequest,
  ScenarioResponse,
} from "./types";

export const useSimulate = () =>
  useMutation({
    mutationFn: (body: ScenarioRequest) =>
      api.post<ScenarioResponse>("/scenarios/simulate", body),
  });

export const useNarrative = () =>
  useMutation({
    mutationFn: (scenario: ScenarioResponse) =>
      api.post<NarrativeResponse>("/scenarios/narrative", { scenario }),
  });
