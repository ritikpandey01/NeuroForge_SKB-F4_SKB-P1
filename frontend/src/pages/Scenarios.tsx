import { useEffect, useMemo, useState } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, LoadingState } from "@/components/common/LoadingState";
import { useSimulate } from "@/features/scenarios/api";
import { LeverPanel } from "@/features/scenarios/LeverPanel";
import { NarrativePanel } from "@/features/scenarios/NarrativePanel";
import { TrajectoryChart } from "@/features/scenarios/TrajectoryChart";
import { LEVER_LABELS, ZERO_LEVERS } from "@/features/scenarios/types";
import type { LeverName, Levers } from "@/features/scenarios/types";
import { fmtInr, fmtPct, fmtTonnes } from "@/lib/formatters";

const DEBOUNCE_MS = 180;

export default function Scenarios() {
  const [levers, setLevers] = useState<Levers>({ ...ZERO_LEVERS });
  const [targetYear, setTargetYear] = useState<number>(2050);
  const [carbonPrice, setCarbonPrice] = useState<number>(2000);
  const simulate = useSimulate();
  const [lastData, setLastData] = useState(simulate.data ?? null);

  useEffect(() => {
    const t = setTimeout(() => {
      simulate.mutate(
        {
          target_year: targetYear,
          levers,
          carbon_price_inr_per_tonne: carbonPrice,
        },
        { onSuccess: (d) => setLastData(d) },
      );
    }, DEBOUNCE_MS);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [levers, targetYear, carbonPrice]);

  const data = lastData;
  const totalDelta = data?.scope_deltas_pct["total"] ?? 0;
  const targetTotal = data?.scenario[data.scenario.length - 1]?.total ?? 0;
  const sbtiTarget = data?.sbti[data.sbti.length - 1]?.total ?? 0;

  const topContribs = useMemo(
    () =>
      (data?.lever_contributions ?? [])
        .slice()
        .sort((a, b) => b.avoided_tonnes - a.avoided_tonnes)
        .slice(0, 3),
    [data],
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
          Scenario Simulator
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Model a decarbonization trajectory from the current baseline to a target year.
          Adjust the five operational levers and compare against a 1.5°C-aligned SBTi pathway.
          The math is deterministic; the AI narrative is an optional second pass.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Levers</CardTitle>
          </CardHeader>
          <CardContent>
            <LeverPanel
              levers={levers}
              targetYear={targetYear}
              carbonPrice={carbonPrice}
              onLeversChange={setLevers}
              onTargetYearChange={setTargetYear}
              onCarbonPriceChange={setCarbonPrice}
            />
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>
                Trajectory {data ? `${data.baseline_year} → ${data.target_year}` : ""}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {simulate.isError && !data && <ErrorState error={simulate.error} />}
              {!data && simulate.isPending && <LoadingState label="Running simulation…" />}
              {data && (
                <>
                  <div className="mb-3 grid grid-cols-3 gap-3">
                    <HeadlineTile
                      label="Baseline"
                      value={fmtTonnes(data.baseline_total_tonnes)}
                      sub={`FY${data.baseline_year}`}
                    />
                    <HeadlineTile
                      label={`Scenario ${data.target_year}`}
                      value={fmtTonnes(targetTotal)}
                      sub={`${totalDelta >= 0 ? "+" : ""}${fmtPct(totalDelta)} vs baseline`}
                      accent={totalDelta < 0 ? "text-success" : "text-slate-800"}
                    />
                    <HeadlineTile
                      label={`SBTi ${data.target_year}`}
                      value={fmtTonnes(sbtiTarget)}
                      sub={
                        targetTotal <= sbtiTarget + 1
                          ? "On / ahead of pathway"
                          : `${fmtTonnes(targetTotal - sbtiTarget)} gap`
                      }
                      accent={targetTotal <= sbtiTarget + 1 ? "text-success" : "text-danger"}
                    />
                  </div>
                  <TrajectoryChart data={data} />
                  <div className="mt-4 grid gap-3 md:grid-cols-3">
                    <ScopeDeltaCell
                      label="Scope 1"
                      pct={data.scope_deltas_pct["scope_1"] ?? 0}
                    />
                    <ScopeDeltaCell
                      label="Scope 2"
                      pct={data.scope_deltas_pct["scope_2"] ?? 0}
                    />
                    <ScopeDeltaCell
                      label="Scope 3"
                      pct={data.scope_deltas_pct["scope_3"] ?? 0}
                    />
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {data && topContribs.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Top lever contributions (at {data.target_year})</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-xs">
                  {topContribs.map((c) => (
                    <li
                      key={c.lever}
                      className="flex items-center justify-between rounded-md border border-slate-100 bg-slate-50/60 px-3 py-2"
                    >
                      <div>
                        <div className="font-medium text-slate-800">
                          {LEVER_LABELS[c.lever as LeverName]?.title ?? c.lever}
                        </div>
                        <div className="text-[10px] uppercase tracking-wider text-slate-400">
                          {LEVER_LABELS[c.lever as LeverName]?.affects ?? ""}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-mono font-semibold text-slate-800">
                          {fmtTonnes(c.avoided_tonnes)}
                        </div>
                        <div className="text-[10px] text-slate-500">
                          {c.pct_of_baseline.toFixed(1)}% of baseline
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {data && data.exposure_by_year.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>
                  Carbon exposure ·{" "}
                  @ ₹{data.carbon_price_inr_per_tonne.toLocaleString("en-IN")} / tCO₂e
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="mb-3 grid grid-cols-3 gap-3">
                  <HeadlineTile
                    label="Baseline exposure"
                    value={fmtInr(data.baseline_total_exposure_inr)}
                    sub={`Cumulative ${data.baseline_year}–${data.target_year}`}
                  />
                  <HeadlineTile
                    label="Scenario exposure"
                    value={fmtInr(data.scenario_total_exposure_inr)}
                    sub="With levers applied"
                  />
                  <HeadlineTile
                    label="Savings"
                    value={fmtInr(data.total_savings_inr)}
                    sub="vs. do-nothing baseline"
                    accent={
                      data.total_savings_inr > 0 ? "text-success" : "text-slate-800"
                    }
                  />
                </div>
                <div className="text-[11px] text-slate-500">
                  Shadow pricing applies a policy/market-equivalent cost to each emitted
                  tonne. Use the input in Levers to model CBAM, EU-ETS, or an internal price.
                </div>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Transition narrative</CardTitle>
            </CardHeader>
            <CardContent>
              <NarrativePanel scenario={data} />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function HeadlineTile({
  label,
  value,
  sub,
  accent,
}: {
  label: string;
  value: string;
  sub: string;
  accent?: string;
}) {
  return (
    <div className="rounded-lg border border-slate-100 bg-slate-50/60 px-3 py-2">
      <div className="text-[10px] font-semibold uppercase tracking-widest text-slate-400">
        {label}
      </div>
      <div className={`mt-1 text-base font-semibold ${accent ?? "text-slate-800"}`}>{value}</div>
      <div className="text-[10px] text-slate-500">{sub}</div>
    </div>
  );
}

function ScopeDeltaCell({ label, pct }: { label: string; pct: number }) {
  const isReduction = pct < 0;
  return (
    <div className="rounded-md border border-slate-200 bg-white px-3 py-2">
      <div className="text-[10px] font-semibold uppercase tracking-widest text-slate-400">
        {label}
      </div>
      <div
        className={`mt-1 font-mono text-sm font-semibold ${isReduction ? "text-success" : "text-slate-700"}`}
      >
        {pct >= 0 ? "+" : ""}
        {pct.toFixed(1)}%
      </div>
    </div>
  );
}
