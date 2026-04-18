import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { MonthlyPoint } from "@/features/emissions/types";

type Props = { data: MonthlyPoint[] };

export function MonthlyTrend({ data }: Props) {
  const rows = data.map((d) => ({
    period: d.period,
    "Scope 1": Math.round(d.scope_1),
    "Scope 2": Math.round(d.scope_2),
    "Scope 3": Math.round(d.scope_3),
  }));
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={rows} margin={{ top: 8, right: 12, left: 0, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
        <XAxis
          dataKey="period"
          fontSize={11}
          tick={{ fill: "#64748B" }}
          interval="preserveStartEnd"
        />
        <YAxis
          fontSize={11}
          tick={{ fill: "#64748B" }}
          tickFormatter={(v) => `${(v / 1000).toFixed(1)}k`}
          label={{ value: "tCO₂e", angle: -90, position: "insideLeft", fontSize: 11, fill: "#64748B" }}
        />
        <Tooltip
          contentStyle={{ borderRadius: 8, fontSize: 12 }}
          formatter={(v: number) => `${v.toLocaleString()} tCO₂e`}
        />
        <Legend iconType="circle" wrapperStyle={{ fontSize: 12 }} />
        <Bar dataKey="Scope 1" stackId="s" fill="#0F766E" />
        <Bar dataKey="Scope 2" stackId="s" fill="#14B8A6" />
        <Bar dataKey="Scope 3" stackId="s" fill="#5EEAD4" />
      </BarChart>
    </ResponsiveContainer>
  );
}
