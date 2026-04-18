import { CalendarDays } from "lucide-react";

import { usePeriod } from "@/contexts/PeriodContext";

export function PeriodSelector() {
  const { period, setPeriod, periods } = usePeriod();
  return (
    <label className="inline-flex items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700">
      <CalendarDays size={14} className="text-slate-400" />
      <select
        className="bg-transparent text-sm outline-none"
        value={period.label}
        onChange={(e) => {
          const next = periods.find((p) => p.label === e.target.value);
          if (next) setPeriod(next);
        }}
      >
        {periods.map((p) => (
          <option key={p.label} value={p.label}>
            {p.label}
          </option>
        ))}
      </select>
    </label>
  );
}
