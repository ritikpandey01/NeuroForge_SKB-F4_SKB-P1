import { AlertTriangle, Factory, ShieldCheck, Users } from "lucide-react";

import { KpiCard } from "@/components/common/KpiCard";
import { ErrorState, LoadingState } from "@/components/common/LoadingState";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fmtPct, fmtTonnes } from "@/lib/formatters";

import { useOperationsDashboard } from "./api";

function dqTone(pct: number): string {
  if (pct >= 70) return "bg-emerald-500";
  if (pct >= 40) return "bg-amber-500";
  return "bg-red-500";
}

export function OperationsView() {
  const q = useOperationsDashboard();

  if (q.isLoading) return <LoadingState label="Loading operations view…" />;
  if (q.isError) return <ErrorState error={q.error} />;
  if (!q.data) return null;

  const d = q.data;
  const rowsDelta = d.activity_rows_this_period - d.activity_rows_prior_period;
  const sc = d.supplier_compliance;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-slate-900">
          Operations view · FY{d.current_year}
        </h2>
        <p className="text-sm text-slate-500">
          Per-site roll-up · data quality · supplier compliance
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          label="Facilities reporting"
          value={String(d.facilities.length)}
          sublabel={`${d.activity_rows_this_period} activity rows this period`}
          icon={<Factory size={20} />}
        />
        <KpiCard
          label="Activity rows Δ vs prior"
          value={`${rowsDelta >= 0 ? "+" : ""}${rowsDelta}`}
          sublabel={`${d.activity_rows_prior_period} rows in FY${d.current_year - 1}`}
          icon={<ShieldCheck size={20} />}
        />
        <KpiCard
          label={`Supplier compliance · ${sc.current_quarter}`}
          value={fmtPct(sc.compliance_pct)}
          sublabel={`${sc.submissions_received} of ${sc.total_suppliers} submitted`}
          icon={<Users size={20} />}
        />
        <KpiCard
          label="Open anomalies"
          value={String(
            d.facilities.reduce((s, f) => s + f.open_anomaly_count, 0),
          )}
          sublabel="Across all facilities"
          icon={<AlertTriangle size={20} />}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Facilities · FY{d.current_year}</CardTitle>
        </CardHeader>
        <CardContent>
          {d.facilities.length === 0 ? (
            <div className="py-6 text-center text-sm text-slate-400">
              No facilities yet.
            </div>
          ) : (
            <div className="overflow-hidden rounded-md border border-slate-200">
              <table className="w-full text-sm">
                <thead className="bg-slate-50 text-[10px] uppercase tracking-widest text-slate-500">
                  <tr>
                    <th className="px-3 py-2 text-left">Facility</th>
                    <th className="px-3 py-2 text-right">Emissions</th>
                    <th className="px-3 py-2 text-right">Share</th>
                    <th className="px-3 py-2 text-left">Data quality</th>
                    <th className="px-3 py-2 text-right">Activity rows</th>
                    <th className="px-3 py-2 text-right">Open anomalies</th>
                  </tr>
                </thead>
                <tbody>
                  {d.facilities.map((f) => (
                    <tr
                      key={f.facility_id}
                      className="border-t border-slate-100 hover:bg-slate-50/40"
                    >
                      <td className="px-3 py-2">
                        <div className="font-medium text-slate-800">
                          {f.name}
                        </div>
                        <div className="text-xs text-slate-500">
                          {f.location}
                        </div>
                      </td>
                      <td className="px-3 py-2 text-right font-mono text-xs text-slate-700">
                        {fmtTonnes(f.total_tonnes)}
                      </td>
                      <td className="px-3 py-2 text-right text-xs text-slate-500">
                        {fmtPct(f.pct_of_total)}
                      </td>
                      <td className="px-3 py-2">
                        <div className="flex items-center gap-2">
                          <div className="h-1.5 w-20 rounded-full bg-slate-100">
                            <div
                              className={`h-1.5 rounded-full ${dqTone(f.data_quality_pct)}`}
                              style={{
                                width: `${Math.min(100, f.data_quality_pct)}%`,
                              }}
                            />
                          </div>
                          <span className="text-xs text-slate-600">
                            {fmtPct(f.data_quality_pct, 0)}
                          </span>
                        </div>
                      </td>
                      <td className="px-3 py-2 text-right font-mono text-xs text-slate-600">
                        {f.activity_row_count}
                      </td>
                      <td className="px-3 py-2 text-right">
                        {f.open_anomaly_count > 0 ? (
                          <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-800">
                            <AlertTriangle size={10} />
                            {f.open_anomaly_count}
                          </span>
                        ) : (
                          <span className="text-xs text-slate-400">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Supplier compliance · {sc.current_quarter}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-slate-600">Submissions received</span>
              <span className="font-mono text-slate-900">
                {sc.submissions_received} / {sc.total_suppliers}
              </span>
            </div>
            <div className="h-2 rounded-full bg-slate-100">
              <div
                className="h-2 rounded-full bg-brand"
                style={{ width: `${Math.min(100, sc.compliance_pct)}%` }}
              />
            </div>
            <div className="text-xs text-slate-500">
              {fmtPct(sc.compliance_pct)} of engaged suppliers have submitted
              for {sc.current_quarter}.
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
