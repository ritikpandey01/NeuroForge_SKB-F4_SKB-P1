import { Activity, Leaf, ShieldCheck, X } from "lucide-react";
import { useMemo, useState } from "react";

import { DataQualityDot } from "@/components/common/DataQualityDot";
import { KpiCard } from "@/components/common/KpiCard";
import { EmptyState, ErrorState, LoadingState } from "@/components/common/LoadingState";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { usePeriod } from "@/contexts/PeriodContext";
import { useFacilities } from "@/features/activities/api";
import {
  useEmissionMethodology,
  useEmissionsList,
  useEmissionsSummary,
} from "@/features/emissions/api";
import { fmtPct, fmtTonnesCompact } from "@/lib/formatters";
import { cn } from "@/lib/utils";

type ScopeFilter = "" | "1" | "2" | "3";

const dqLevel = (score: number, verified: boolean): "verified" | "estimated" | "flagged" => {
  if (verified && score >= 4) return "verified";
  if (score <= 2) return "flagged";
  return "estimated";
};

export default function Emissions() {
  const { period } = usePeriod();
  const facilities = useFacilities();
  const [scope, setScope] = useState<ScopeFilter>("");
  const [facilityId, setFacilityId] = useState<number | undefined>(undefined);
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const params = {
    scope: scope ? Number(scope) : undefined,
    facility_id: facilityId,
    period_start: period.start,
    period_end: period.end,
  };

  const summary = useEmissionsSummary({
    facility_id: facilityId,
    period_start: period.start,
    period_end: period.end,
  });
  const ledger = useEmissionsList({ ...params, limit: 500 });

  const scopeTotals = useMemo(() => {
    const m = new Map<number, number>();
    (summary.data?.by_scope ?? []).forEach((s) => m.set(s.scope, s.co2e_tonnes));
    return m;
  }, [summary.data]);

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Emissions ledger</h1>
          <p className="mt-1 text-sm text-slate-500">
            Every calculated emission with full methodology — click any row for factor,
            formula, and data-quality detail.
          </p>
        </div>
        <div className="text-xs text-slate-500">
          Period: <span className="font-medium text-slate-700">{period.label}</span>
        </div>
      </header>

      <section className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <KpiCard
          label="Total emissions"
          value={summary.data ? fmtTonnesCompact(summary.data.total_co2e_tonnes) : "—"}
          sublabel={period.label}
          icon={<Leaf size={18} />}
        />
        <KpiCard
          label="Scope 1"
          value={fmtTonnesCompact(scopeTotals.get(1) ?? 0)}
          sublabel="Direct / combustion / process"
          icon={<Activity size={18} />}
        />
        <KpiCard
          label="Scope 2"
          value={fmtTonnesCompact(scopeTotals.get(2) ?? 0)}
          sublabel="Purchased electricity"
          icon={<Activity size={18} />}
        />
        <KpiCard
          label="Verified data"
          value={summary.data ? fmtPct(summary.data.data_quality_verified_pct, 0) : "—"}
          sublabel="Rows with primary evidence"
          icon={<ShieldCheck size={18} />}
        />
      </section>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Filter ledger</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-center gap-3 text-xs">
            <label className="flex items-center gap-2">
              <span className="text-slate-500">Scope:</span>
              <select
                className="rounded-md border border-slate-200 bg-white px-2 py-1"
                value={scope}
                onChange={(e) => setScope(e.target.value as ScopeFilter)}
              >
                <option value="">All</option>
                <option value="1">Scope 1</option>
                <option value="2">Scope 2</option>
                <option value="3">Scope 3</option>
              </select>
            </label>
            <label className="flex items-center gap-2">
              <span className="text-slate-500">Facility:</span>
              <select
                className="rounded-md border border-slate-200 bg-white px-2 py-1"
                value={facilityId ?? ""}
                onChange={(e) =>
                  setFacilityId(e.target.value ? Number(e.target.value) : undefined)
                }
              >
                <option value="">All</option>
                {(facilities.data ?? []).map((f) => (
                  <option key={f.id} value={f.id}>
                    {f.name}
                  </option>
                ))}
              </select>
            </label>
            <span className="ml-auto text-slate-400">
              {ledger.data?.length ?? 0} rows · max 500
            </span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-5">
          {ledger.isLoading && <LoadingState label="Loading emissions ledger…" />}
          {ledger.isError && <ErrorState error={ledger.error} />}
          {ledger.data && ledger.data.length === 0 && (
            <EmptyState message="No emissions match these filters." />
          )}

          {ledger.data && ledger.data.length > 0 && (
            <div className="overflow-x-auto rounded-md border border-slate-200">
              <table className="min-w-full divide-y divide-slate-200 text-xs">
                <thead className="bg-slate-50 text-slate-500">
                  <tr>
                    <Th>#</Th>
                    <Th>Period</Th>
                    <Th>Facility</Th>
                    <Th>Scope</Th>
                    <Th>Category</Th>
                    <Th>Subcategory</Th>
                    <Th className="text-right">Quantity</Th>
                    <Th>Unit</Th>
                    <Th className="text-right">tCO₂e</Th>
                    <Th>Source</Th>
                    <Th>DQ</Th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {ledger.data.map((r) => (
                    <tr
                      key={r.id}
                      onClick={() => setSelectedId(r.id)}
                      className={cn(
                        "cursor-pointer hover:bg-slate-50/80",
                        selectedId === r.id && "bg-brand/5",
                      )}
                    >
                      <Td>#{r.id}</Td>
                      <Td className="whitespace-nowrap">
                        {r.period_start} → {r.period_end}
                      </Td>
                      <Td>{r.facility_name}</Td>
                      <Td>{r.scope}</Td>
                      <Td>{r.category}</Td>
                      <Td className="font-mono">{r.subcategory}</Td>
                      <Td className="text-right font-mono">
                        {r.quantity.toLocaleString("en-IN", { maximumFractionDigits: 1 })}
                      </Td>
                      <Td>{r.unit}</Td>
                      <Td className="text-right font-mono font-medium">
                        {r.co2e_tonnes.toLocaleString("en-IN", { maximumFractionDigits: 2 })}
                      </Td>
                      <Td className="max-w-[180px] text-slate-500">
                        <span title={r.factor_source ?? ""} className="block truncate">
                          {r.factor_source ?? "—"}
                        </span>
                      </Td>
                      <Td>
                        <DataQualityDot level={dqLevel(r.data_quality_score, r.verified)} />
                      </Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {selectedId !== null && (
        <MethodologyDrawer id={selectedId} onClose={() => setSelectedId(null)} />
      )}
    </div>
  );
}

function MethodologyDrawer({ id, onClose }: { id: number; onClose: () => void }) {
  const q = useEmissionMethodology(id);
  const m = q.data;

  return (
    <div className="fixed inset-0 z-50 flex" role="dialog">
      <div
        className="flex-1 bg-slate-900/30 backdrop-blur-[1px]"
        onClick={onClose}
        aria-label="Close methodology"
      />
      <aside className="flex w-full max-w-md flex-col overflow-y-auto border-l border-slate-200 bg-white shadow-2xl">
        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
          <div>
            <div className="text-xs uppercase tracking-wide text-slate-500">Methodology</div>
            <div className="text-sm font-semibold text-slate-900">Emission #{id}</div>
          </div>
          <button
            onClick={onClose}
            className="rounded-md p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
            aria-label="Close"
          >
            <X size={16} />
          </button>
        </div>

        <div className="flex-1 px-5 py-4 text-sm">
          {q.isLoading && <LoadingState label="Loading methodology…" />}
          {q.isError && <ErrorState error={q.error} />}
          {m && (
            <div className="space-y-5">
              <Section title="Activity">
                <Row k="Description" v={m.activity_description} />
                <Row k="Scope" v={`Scope ${m.scope}`} />
                <Row k="Category" v={`${m.category} / ${m.subcategory}`} mono />
                <Row
                  k="Quantity"
                  v={`${m.quantity.toLocaleString("en-IN", { maximumFractionDigits: 2 })} ${m.unit}`}
                  mono
                />
                <Row k="Period" v={`${m.period_start} → ${m.period_end}`} />
              </Section>

              <Section title="Emission factor">
                {m.factor_id ? (
                  <>
                    <Row k="Source" v={m.factor_source ?? "—"} />
                    <Row k="Year" v={m.factor_year ?? "—"} />
                    <Row
                      k="Value"
                      v={`${m.factor_value?.toLocaleString("en-IN", { maximumFractionDigits: 4 })} ${m.factor_unit ?? ""}`}
                      mono
                    />
                  </>
                ) : (
                  <div className="text-xs text-slate-500">No factor linked.</div>
                )}
              </Section>

              <Section title="Calculation">
                <Row k="Method" v={m.calculation_method} mono />
                <Row
                  k="Formula"
                  v={
                    m.factor_value
                      ? `${m.quantity.toLocaleString("en-IN")} × ${m.factor_value} = ${m.co2e_kg.toLocaleString("en-IN", { maximumFractionDigits: 2 })} kg`
                      : `${m.co2e_kg.toLocaleString("en-IN", { maximumFractionDigits: 2 })} kg`
                  }
                  mono
                />
                <Row
                  k="Result"
                  v={`${m.co2e_tonnes.toLocaleString("en-IN", { maximumFractionDigits: 3 })} tCO₂e`}
                  emphasis
                />
              </Section>

              <Section title="Data quality">
                <Row k="DQ score" v={`${m.data_quality_score} / 5`} mono />
                <Row k="Verified" v={m.verified ? "Yes" : "No"} />
              </Section>
            </div>
          )}
        </div>
      </aside>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
        {title}
      </div>
      <dl className="divide-y divide-slate-100 rounded-md border border-slate-200">
        {children}
      </dl>
    </div>
  );
}

function Row({
  k,
  v,
  mono,
  emphasis,
}: {
  k: string;
  v: React.ReactNode;
  mono?: boolean;
  emphasis?: boolean;
}) {
  return (
    <div className="flex items-start justify-between gap-3 px-3 py-2 text-xs">
      <dt className="text-slate-500">{k}</dt>
      <dd
        className={cn(
          "text-right text-slate-800",
          mono && "font-mono",
          emphasis && "font-semibold text-brand",
        )}
      >
        {v}
      </dd>
    </div>
  );
}

function Th({ children, className }: { children?: React.ReactNode; className?: string }) {
  return (
    <th
      className={cn(
        "px-3 py-2 text-left text-[10px] font-semibold uppercase tracking-wide",
        className,
      )}
    >
      {children}
    </th>
  );
}

function Td({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <td className={cn("px-3 py-1.5 align-top text-slate-700", className)}>{children}</td>
  );
}
