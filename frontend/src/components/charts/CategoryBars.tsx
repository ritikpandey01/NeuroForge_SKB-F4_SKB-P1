import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { CategoryBreakdown } from "@/features/emissions/types";

type Props = { data: CategoryBreakdown[]; limit?: number };

const SCOPE_COLOR: Record<number, string> = { 1: "#0F766E", 2: "#14B8A6", 3: "#5EEAD4" };

export function CategoryBars({ data, limit = 5 }: Props) {
  const rows = data.slice(0, limit).map((d) => ({
    label: `S${d.scope} · ${d.category}`,
    tCO2e: Math.round(d.co2e_tonnes),
    scope: d.scope,
  }));
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={rows} layout="vertical" margin={{ top: 8, right: 24, left: 16, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
        <XAxis
          type="number"
          fontSize={11}
          tick={{ fill: "#64748B" }}
          tickFormatter={(v) => `${(v / 1000).toFixed(1)}k`}
        />
        <YAxis
          type="category"
          dataKey="label"
          fontSize={11}
          tick={{ fill: "#64748B" }}
          width={160}
        />
        <Tooltip
          contentStyle={{ borderRadius: 8, fontSize: 12 }}
          formatter={(v: number) => `${v.toLocaleString()} tCO₂e`}
        />
        <Bar dataKey="tCO2e" radius={[0, 4, 4, 0]}>
          {rows.map((r, i) => (
            <rect key={i} fill={SCOPE_COLOR[r.scope]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
