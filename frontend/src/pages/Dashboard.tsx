import { Activity, Leaf, ShieldCheck, TrendingDown } from "lucide-react";
import { useState } from "react";

import { CategoryBars } from "@/components/charts/CategoryBars";
import { FacilityBars } from "@/components/charts/FacilityBars";
import { MonthlyTrend } from "@/components/charts/MonthlyTrend";
import { ScopeDonut } from "@/components/charts/ScopeDonut";
import { DataQualityDot } from "@/components/common/DataQualityDot";
import { KpiCard } from "@/components/common/KpiCard";
import { ErrorState, LoadingState } from "@/components/common/LoadingState";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { usePeriod } from "@/contexts/PeriodContext";
import { ExecutiveView } from "@/features/dashboards/ExecutiveView";
import { OperationsView } from "@/features/dashboards/OperationsView";
import { useEmissionsSummary } from "@/features/emissions/api";
import { fmtPct, fmtTonnes } from "@/lib/formatters";
import { cn } from "@/lib/utils";

type TabKey = "executive" | "operations" | "emissions";

const TABS: { key: TabKey; label: string; hint: string }[] = [
  { key: "executive", label: "Executive", hint: "Board-level view" },
  { key: "operations", label: "Operations", hint: "Per-site roll-up" },
  { key: "emissions", label: "Emissions", hint: "Analytical detail" },
];

export default function Dashboard() {
  const [tab, setTab] = useState<TabKey>("executive");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
          Governance Dashboard
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Pre-composed views for C-suite, ESG ops, and analysts
        </p>
      </div>

      <div className="inline-flex rounded-md border border-slate-200 bg-white p-1 text-sm">
        {TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            onClick={() => setTab(t.key)}
            title={t.hint}
            className={cn(
              "rounded px-4 py-1.5 font-medium transition-colors",
              tab === t.key
                ? "bg-brand text-white"
                : "text-slate-600 hover:text-slate-900",
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "executive" && <ExecutiveView />}
      {tab === "operations" && <OperationsView />}
      {tab === "emissions" && <EmissionsView />}
    </div>
  );
}

function EmissionsView() {
  const { period } = usePeriod();
  const query = useEmissionsSummary({
    period_start: period.start,
    period_end: period.end,
  });

  if (query.isLoading) return <LoadingState label="Loading emissions summary…" />;
  if (query.isError) return <ErrorState error={query.error} />;
  if (!query.data) return null;

  const d = query.data;
  const scope3 = d.by_scope.find((s) => s.scope === 3);
  const qualityLevel =
    d.data_quality_verified_pct >= 70
      ? "verified"
      : d.data_quality_verified_pct >= 40
        ? "estimated"
        : "flagged";

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-slate-900">
          Emissions analytics
        </h2>
        <p className="text-sm text-slate-500">
          {period.label} · GHG Protocol Scope 1 + 2 + 3
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          label="Total emissions"
          value={fmtTonnes(d.total_co2e_tonnes)}
          sublabel="All scopes"
          icon={<Leaf size={20} />}
        />
        <KpiCard
          label="Scope 3 share"
          value={scope3 ? fmtPct(scope3.pct_of_total) : "—"}
          sublabel="Value-chain emissions"
          icon={<Activity size={20} />}
        />
        <KpiCard
          label="Data quality"
          value={fmtPct(d.data_quality_verified_pct)}
          sublabel="Verified activity data"
          icon={<ShieldCheck size={20} />}
        />
        <KpiCard
          label="Facilities reporting"
          value={String(d.by_facility.length)}
          sublabel="Across India"
          icon={<TrendingDown size={20} />}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Scope 1 / 2 / 3 breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <ScopeDonut data={d.by_scope} />
            <div className="mt-3 space-y-1 text-xs">
              {d.by_scope.map((s) => (
                <div key={s.scope} className="flex justify-between text-slate-600">
                  <span>Scope {s.scope}</span>
                  <span className="font-medium text-slate-900">
                    {fmtTonnes(s.co2e_tonnes)} · {fmtPct(s.pct_of_total)}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Monthly emissions trend (stacked by scope)</CardTitle>
          </CardHeader>
          <CardContent>
            {d.monthly.length === 0 ? (
              <div className="py-12 text-center text-sm text-slate-400">
                No monthly data for this period
              </div>
            ) : (
              <MonthlyTrend data={d.monthly} />
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Facility-wise comparison</CardTitle>
          </CardHeader>
          <CardContent>
            <FacilityBars data={d.by_facility} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Top 5 emission categories</CardTitle>
          </CardHeader>
          <CardContent>
            <CategoryBars data={d.by_category} limit={5} />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Data quality indicator</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <DataQualityDot level={qualityLevel} withLabel />
            <div className="flex-1">
              <div className="h-2 rounded-full bg-slate-100">
                <div
                  className="h-2 rounded-full bg-brand transition-all"
                  style={{ width: `${Math.min(100, d.data_quality_verified_pct)}%` }}
                />
              </div>
              <div className="mt-1 text-xs text-slate-500">
                {fmtPct(d.data_quality_verified_pct)} of activity data is verified;
                the rest is estimated from spend-based or activity-based factors.
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
