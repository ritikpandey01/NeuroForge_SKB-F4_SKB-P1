import { ErrorState, LoadingState } from "@/components/common/LoadingState";

import { useImpactMatrix } from "./api";
import type { MatrixCell, MaturityLevel, SpendBucket } from "./types";

const SPEND_BUCKETS: SpendBucket[] = ["high", "medium", "low"];
const MATURITY_COLS: MaturityLevel[] = [
  "spend_based",
  "activity_based",
  "verified_primary",
];

const MATURITY_LABELS: Record<MaturityLevel, string> = {
  spend_based: "Spend-based",
  activity_based: "Activity-based",
  verified_primary: "Verified primary",
};

const SPEND_LABELS: Record<SpendBucket, string> = {
  low: "Low spend",
  medium: "Medium spend",
  high: "High spend",
};

// Risk color — high spend + spend-based (low maturity) = highest engagement priority.
// Low spend + verified primary = already in good shape.
function riskClass(spend: SpendBucket, maturity: MaturityLevel): string {
  const spendScore = spend === "high" ? 2 : spend === "medium" ? 1 : 0;
  const maturityScore =
    maturity === "spend_based" ? 2 : maturity === "activity_based" ? 1 : 0;
  const total = spendScore + maturityScore;
  if (total >= 4) return "bg-red-100 border-red-300 text-red-900";
  if (total >= 3) return "bg-amber-100 border-amber-300 text-amber-900";
  if (total >= 2) return "bg-yellow-50 border-yellow-200 text-yellow-900";
  if (total >= 1) return "bg-emerald-50 border-emerald-200 text-emerald-900";
  return "bg-slate-50 border-slate-200 text-slate-700";
}

function riskLabel(spend: SpendBucket, maturity: MaturityLevel): string {
  const spendScore = spend === "high" ? 2 : spend === "medium" ? 1 : 0;
  const maturityScore =
    maturity === "spend_based" ? 2 : maturity === "activity_based" ? 1 : 0;
  const total = spendScore + maturityScore;
  if (total >= 4) return "Critical — engage now";
  if (total >= 3) return "High priority";
  if (total >= 2) return "Monitor";
  if (total >= 1) return "On track";
  return "Best-in-class";
}

export function ImpactMatrix() {
  const matrix = useImpactMatrix();

  if (matrix.isLoading) return <LoadingState label="Loading impact matrix…" />;
  if (matrix.isError) return <ErrorState error={matrix.error} />;
  if (!matrix.data) return null;

  const { cells, spend_thresholds, total_suppliers, total_spend } = matrix.data;
  const grid = new Map<string, MatrixCell>();
  for (const c of cells) {
    grid.set(`${c.spend_bucket}:${c.data_maturity_level}`, c);
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-x-6 gap-y-1 text-xs text-slate-500">
        <span>
          <span className="font-medium text-slate-700">{total_suppliers}</span> suppliers ·{" "}
          ₹
          <span className="font-medium text-slate-700">
            {total_spend.toLocaleString("en-IN", { maximumFractionDigits: 1 })}
          </span>{" "}
          Cr total spend
        </span>
        <span>
          Bucket thresholds: low ≤ ₹{spend_thresholds.low_max} Cr · medium ≤ ₹
          {spend_thresholds.medium_max} Cr
        </span>
      </div>

      <div className="overflow-x-auto rounded-md border border-slate-200">
        <table className="min-w-full border-collapse">
          <thead>
            <tr className="bg-slate-50 text-[11px] font-medium uppercase tracking-wide text-slate-500">
              <th className="w-36 px-3 py-2 text-left">Spend ↓ · Maturity →</th>
              {MATURITY_COLS.map((m) => (
                <th key={m} className="px-3 py-2 text-left">
                  {MATURITY_LABELS[m]}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {SPEND_BUCKETS.map((spend) => (
              <tr key={spend} className="border-t border-slate-100">
                <th className="px-3 py-3 text-left text-xs font-semibold uppercase text-slate-600">
                  {SPEND_LABELS[spend]}
                </th>
                {MATURITY_COLS.map((maturity) => {
                  const cell = grid.get(`${spend}:${maturity}`);
                  const count = cell?.supplier_count ?? 0;
                  const spendTotal = cell?.total_spend ?? 0;
                  return (
                    <td
                      key={maturity}
                      className={`border border-slate-200 px-3 py-3 align-top ${riskClass(
                        spend,
                        maturity,
                      )}`}
                    >
                      <div className="flex items-baseline justify-between">
                        <span className="text-xl font-semibold">{count}</span>
                        <span className="text-[10px] font-medium uppercase tracking-wide opacity-70">
                          {riskLabel(spend, maturity)}
                        </span>
                      </div>
                      <div className="mt-1 text-[11px] opacity-80">
                        ₹{spendTotal.toLocaleString("en-IN", { maximumFractionDigits: 1 })} Cr
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="rounded-md bg-slate-50 p-3 text-xs text-slate-600">
        <span className="font-medium text-slate-700">Read this matrix like a portfolio risk map.</span>{" "}
        Suppliers in the top-left cell (high spend · spend-based data) drive the most emissions
        but report via the lowest-quality method — they're the highest ROI for engagement. The
        bottom-right cell is your already-mature tail.
      </div>
    </div>
  );
}
