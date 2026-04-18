import { ReactNode } from "react";

import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type Props = {
  label: string;
  value: string;
  sublabel?: string;
  trend?: { value: string; up?: boolean } | null;
  icon?: ReactNode;
  className?: string;
};

export function KpiCard({ label, value, sublabel, trend, icon, className }: Props) {
  return (
    <Card className={cn("", className)}>
      <CardContent className="pt-5">
        <div className="flex items-start justify-between">
          <div>
            <div className="kpi-label">{label}</div>
            <div className="mt-2 kpi-value">{value}</div>
            {sublabel && <div className="mt-1 text-xs text-slate-500">{sublabel}</div>}
          </div>
          {icon && <div className="text-brand">{icon}</div>}
        </div>
        {trend && (
          <div
            className={cn(
              "mt-3 inline-flex items-center gap-1 text-xs font-medium",
              trend.up ? "text-danger" : "text-success",
            )}
          >
            <span>{trend.up ? "▲" : "▼"}</span>
            <span>{trend.value}</span>
            <span className="text-slate-400">vs prev. period</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
