import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { FacilityBreakdown } from "@/features/emissions/types";

type Props = { data: FacilityBreakdown[] };

export function FacilityBars({ data }: Props) {
  const rows = data.map((d) => ({
    facility: d.facility_name,
    tCO2e: Math.round(d.co2e_tonnes),
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
          dataKey="facility"
          fontSize={11}
          tick={{ fill: "#64748B" }}
          width={150}
        />
        <Tooltip
          contentStyle={{ borderRadius: 8, fontSize: 12 }}
          formatter={(v: number) => `${v.toLocaleString()} tCO₂e`}
        />
        <Bar dataKey="tCO2e" fill="#0F766E" radius={[0, 4, 4, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
