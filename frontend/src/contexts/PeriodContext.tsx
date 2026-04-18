import { createContext, ReactNode, useContext, useMemo, useState } from "react";

export type Period = {
  label: string;
  start: string | undefined;
  end: string | undefined;
};

export const PERIODS: Period[] = [
  { label: "All time", start: undefined, end: undefined },
  { label: "FY 2024-25", start: "2024-04-01", end: "2025-03-31" },
  { label: "FY 2025-26", start: "2025-04-01", end: "2026-03-31" },
  { label: "Calendar 2024", start: "2024-01-01", end: "2024-12-31" },
  { label: "Calendar 2025", start: "2025-01-01", end: "2025-12-31" },
];

type Ctx = {
  period: Period;
  setPeriod: (p: Period) => void;
  periods: Period[];
};

const PeriodCtx = createContext<Ctx | null>(null);

export function PeriodProvider({ children }: { children: ReactNode }) {
  const [period, setPeriod] = useState<Period>(PERIODS[0]);
  const value = useMemo(() => ({ period, setPeriod, periods: PERIODS }), [period]);
  return <PeriodCtx.Provider value={value}>{children}</PeriodCtx.Provider>;
}

export function usePeriod() {
  const ctx = useContext(PeriodCtx);
  if (!ctx) throw new Error("usePeriod must be used within PeriodProvider");
  return ctx;
}
