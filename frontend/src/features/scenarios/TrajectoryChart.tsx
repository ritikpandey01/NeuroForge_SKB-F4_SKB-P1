import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { ScenarioResponse } from "./types";

type Props = { data: ScenarioResponse };

export function TrajectoryChart({ data }: Props) {
  const merged = data.scenario.map((p, i) => ({
    year: p.year,
    Scenario: Math.round(p.total),
    Baseline: Math.round(data.baseline[i].total),
    "SBTi 1.5°C": Math.round(data.sbti[i].total),
  }));

  return (
    <ResponsiveContainer width="100%" height={320}>
      <LineChart data={merged} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
        <XAxis dataKey="year" fontSize={11} tick={{ fill: "#64748B" }} />
        <YAxis
          fontSize={11}
          tick={{ fill: "#64748B" }}
          tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
          label={{
            value: "tCO₂e",
            angle: -90,
            position: "insideLeft",
            fontSize: 11,
            fill: "#64748B",
          }}
        />
        <Tooltip
          contentStyle={{ borderRadius: 8, fontSize: 12 }}
          formatter={(v: number) => `${v.toLocaleString()} tCO₂e`}
        />
        <Legend iconType="plainline" wrapperStyle={{ fontSize: 12 }} />
        <Line
          type="monotone"
          dataKey="Baseline"
          stroke="#94A3B8"
          strokeWidth={2}
          dot={false}
          strokeDasharray="2 4"
        />
        <Line
          type="monotone"
          dataKey="Scenario"
          stroke="#0F766E"
          strokeWidth={3}
          dot={false}
        />
        <Line
          type="monotone"
          dataKey="SBTi 1.5°C"
          stroke="#DC2626"
          strokeWidth={2}
          dot={false}
          strokeDasharray="6 4"
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
