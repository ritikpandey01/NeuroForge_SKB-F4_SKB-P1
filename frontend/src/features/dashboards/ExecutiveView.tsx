import {
  AlertTriangle,
  Coins,
  FileText,
  Gavel,
  Leaf,
  ShieldAlert,
  Target,
  TrendingDown,
  TrendingUp,
} from "lucide-react";

import { KpiCard } from "@/components/common/KpiCard";
import { ErrorState, LoadingState } from "@/components/common/LoadingState";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fmtInr, fmtPct, fmtTonnes } from "@/lib/formatters";

import { useExecutiveDashboard } from "./api";

const SEVERITY_STYLES: Record<string, string> = {
  critical: "bg-red-100 text-red-800",
  high: "bg-amber-100 text-amber-800",
  medium: "bg-yellow-50 text-yellow-700",
  low: "bg-slate-100 text-slate-600",
};

export function ExecutiveView() {
  const q = useExecutiveDashboard();

  if (q.isLoading) return <LoadingState label="Loading executive view…" />;
  if (q.isError) return <ErrorState error={q.error} />;
  if (!q.data) return null;

  const d = q.data;
  const yoyUp = d.yoy_delta_pct > 0;
  const gapOver = d.sbti_gap_tonnes > 0;
  const pathwayPctOfBase = d.base_year_total_tonnes
    ? (d.sbti_pathway_target_tonnes / d.base_year_total_tonnes) * 100
    : 0;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-slate-900">{d.org_name}</h2>
        <p className="text-sm text-slate-500">
          Executive view · FY{d.current_year} vs FY{d.prior_year} · base year{" "}
          {d.base_year} · net-zero by {d.net_zero_target_year}
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          label="Total emissions"
          value={fmtTonnes(d.current_total_tonnes)}
          sublabel={`FY${d.current_year} · all scopes`}
          icon={<Leaf size={20} />}
          trend={{
            value: `${d.yoy_delta_pct.toFixed(1)}%`,
            up: yoyUp,
          }}
        />
        <KpiCard
          label="SBTi 1.5°C target"
          value={fmtTonnes(d.sbti_pathway_target_tonnes)}
          sublabel={`${pathwayPctOfBase.toFixed(1)}% of ${d.base_year} baseline`}
          icon={<Target size={20} />}
        />
        <KpiCard
          label={gapOver ? "Over pathway" : "Under pathway"}
          value={fmtTonnes(Math.abs(d.sbti_gap_tonnes))}
          sublabel={gapOver ? "Gap to close" : "Buffer below target"}
          icon={gapOver ? <TrendingUp size={20} /> : <TrendingDown size={20} />}
        />
        <KpiCard
          label="Open risks"
          value={String(d.anomalies_open)}
          sublabel={`${d.reports_generated} reports generated`}
          icon={<AlertTriangle size={20} />}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        <KpiCard
          label="Board attention"
          value={String(d.anomalies_escalated)}
          sublabel={
            d.anomalies_escalated === 0
              ? "No items awaiting board review"
              : "Escalated · awaiting decision"
          }
          icon={<ShieldAlert size={20} />}
        />
        <KpiCard
          label="Board-reviewed"
          value={String(d.anomalies_board_reviewed)}
          sublabel="Closed with board sign-off"
          icon={<Gavel size={20} />}
        />
        <KpiCard
          label="Carbon exposure"
          value={fmtInr(d.carbon_exposure_current_inr)}
          sublabel={`FY${d.current_year} · @ ₹${d.carbon_price_inr_per_tonne.toLocaleString("en-IN")} / tCO₂e`}
          icon={<Coins size={20} />}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Scope mix · FY{d.current_year}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {d.scope_mix.map((s) => (
                <div key={s.scope} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="font-medium text-slate-700">
                      Scope {s.scope}
                    </span>
                    <span className="text-slate-500">
                      {fmtTonnes(s.tonnes)} · {fmtPct(s.pct)}
                    </span>
                  </div>
                  <div className="h-2 rounded-full bg-slate-100">
                    <div
                      className="h-2 rounded-full bg-brand"
                      style={{ width: `${Math.min(100, s.pct)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>SBTi pathway position</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-600">Base year ({d.base_year})</span>
                <span className="font-mono text-slate-900">
                  {fmtTonnes(d.base_year_total_tonnes)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">
                  Pathway target (FY{d.current_year})
                </span>
                <span className="font-mono text-slate-900">
                  {fmtTonnes(d.sbti_pathway_target_tonnes)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Actual (FY{d.current_year})</span>
                <span className="font-mono text-slate-900">
                  {fmtTonnes(d.current_total_tonnes)}
                </span>
              </div>
              <div
                className={`mt-2 rounded-md p-3 text-xs ${
                  gapOver
                    ? "bg-red-50 text-red-800"
                    : "bg-emerald-50 text-emerald-800"
                }`}
              >
                {gapOver ? (
                  <>
                    <b>{fmtTonnes(d.sbti_gap_tonnes)}</b> above the 4.2%/yr
                    linear pathway. Additional reduction needed to stay on track
                    for net-zero by {d.net_zero_target_year}.
                  </>
                ) : (
                  <>
                    <b>{fmtTonnes(Math.abs(d.sbti_gap_tonnes))}</b> below the
                    pathway — on or ahead of SBTi 1.5°C trajectory.
                  </>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Top open risks</CardTitle>
        </CardHeader>
        <CardContent>
          {d.top_risks.length === 0 ? (
            <div className="py-6 text-center text-sm text-slate-400">
              No open critical or high-severity anomalies.
            </div>
          ) : (
            <ul className="divide-y divide-slate-100 text-sm">
              {d.top_risks.map((r) => (
                <li
                  key={r.id}
                  className="flex items-start justify-between gap-4 py-3"
                >
                  <div className="flex-1">
                    <div className="font-medium text-slate-800">{r.title}</div>
                    <div className="mt-0.5 text-xs text-slate-500">
                      {r.detector}
                      {r.facility_id ? ` · facility #${r.facility_id}` : ""}
                    </div>
                  </div>
                  <span
                    className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${
                      SEVERITY_STYLES[r.severity] ?? "bg-slate-100 text-slate-600"
                    }`}
                  >
                    {r.severity}
                  </span>
                </li>
              ))}
            </ul>
          )}
          <div className="mt-3 flex items-center gap-1 text-xs text-slate-500">
            <FileText size={12} />
            {d.reports_generated} compliance reports generated to date
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
