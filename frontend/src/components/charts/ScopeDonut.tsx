import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import type { ScopeBreakdown } from "@/features/emissions/types";

const COLORS = ["#0F766E", "#14B8A6", "#5EEAD4"];

type Props = { data: ScopeBreakdown[] };

export function ScopeDonut({ data }: Props) {
  const rows = data.map((d) => ({
    name: `Scope ${d.scope}`,
    value: Math.round(d.co2e_tonnes),
    pct: d.pct_of_total,
  }));
  return (
    <ResponsiveContainer width="100%" height={260}>
      <PieChart>
        <Pie
          data={rows}
          dataKey="value"
          nameKey="name"
          cx="50%"
          cy="50%"
          innerRadius={55}
          outerRadius={85}
          stroke="white"
          strokeWidth={2}
        >
          {rows.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          formatter={(value: number, _name, item) =>
            [
              `${value.toLocaleString()} tCO₂e (${item.payload.pct.toFixed(1)}%)`,
              item.payload.name,
            ] as [string, string]
          }
          contentStyle={{ borderRadius: 8, fontSize: 12 }}
        />
        <Legend iconType="circle" wrapperStyle={{ fontSize: 12 }} />
      </PieChart>
    </ResponsiveContainer>
  );
}
