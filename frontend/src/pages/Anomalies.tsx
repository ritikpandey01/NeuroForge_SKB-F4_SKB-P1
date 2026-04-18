import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAnomalySummary } from "@/features/anomalies/api";
import { AnomalyFeed } from "@/features/anomalies/AnomalyFeed";

const SEVERITY_COLORS: Record<string, string> = {
  critical: "text-red-600",
  high: "text-orange-600",
  medium: "text-amber-600",
  low: "text-slate-500",
};

export default function Anomalies() {
  const summary = useAnomalySummary();
  const counts = summary.data?.by_severity ?? {};

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
          Anomaly Detection
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Statistical sweep over activity data and supplier submissions. Flags
          z-score outliers, missing reporting periods, zero-emission submissions,
          and sudden spikes. AI generates a plain-English explanation for each
          one — you decide whether to acknowledge, dismiss, or investigate.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
        <SummaryTile label="Open" value={summary.data?.open_count ?? 0} accent="text-slate-900" />
        {(["critical", "high", "medium", "low"] as const).map((s) => (
          <SummaryTile
            key={s}
            label={s}
            value={counts[s] ?? 0}
            accent={SEVERITY_COLORS[s]}
          />
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Feed</CardTitle>
        </CardHeader>
        <CardContent>
          <AnomalyFeed />
        </CardContent>
      </Card>
    </div>
  );
}

function SummaryTile({
  label,
  value,
  accent,
}: {
  label: string;
  value: number;
  accent: string;
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <div className="text-[10px] font-semibold uppercase tracking-widest text-slate-400">
        {label}
      </div>
      <div className={`mt-1 text-2xl font-semibold ${accent}`}>{value}</div>
    </div>
  );
}
