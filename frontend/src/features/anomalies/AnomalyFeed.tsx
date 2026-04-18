import { AlertTriangle, Check, Gavel, ShieldAlert, Sparkles, X } from "lucide-react";
import { useState } from "react";

import { ErrorState, LoadingState } from "@/components/common/LoadingState";
import { Button } from "@/components/ui/button";

import {
  useAnomalies,
  useExplainAnomalies,
  useScanAnomalies,
  useUpdateAnomalyStatus,
} from "./api";
import { EscalationPanel } from "./EscalationPanel";
import type { Anomaly, AnomalyStatus, Detector, Severity } from "./types";

const SEVERITY_STYLES: Record<Severity, string> = {
  critical: "border-l-red-500 bg-red-50",
  high: "border-l-orange-400 bg-orange-50",
  medium: "border-l-amber-300 bg-amber-50",
  low: "border-l-slate-300 bg-slate-50",
};

const SEVERITY_BADGE: Record<Severity, string> = {
  critical: "bg-red-600 text-white",
  high: "bg-orange-500 text-white",
  medium: "bg-amber-400 text-amber-900",
  low: "bg-slate-300 text-slate-700",
};

const STATUS_BADGE: Record<AnomalyStatus, string> = {
  new: "bg-slate-100 text-slate-700",
  acknowledged: "bg-blue-50 text-blue-700",
  dismissed: "bg-slate-100 text-slate-400",
  resolved: "bg-emerald-50 text-emerald-700",
};

const DETECTOR_LABEL: Record<Detector, string> = {
  outlier_zscore: "z-score outlier",
  period_gap: "missing period",
  zero_value: "zero-value report",
  spike_pct: "sudden spike",
};

export function AnomalyFeed() {
  const [severity, setSeverity] = useState<string>("");
  const [status, setStatus] = useState<string>("");
  const [detector, setDetector] = useState<string>("");
  const [escalationStatus, setEscalationStatus] = useState<string>("");

  const list = useAnomalies({
    severity: severity || undefined,
    status: status || undefined,
    detector: detector || undefined,
    escalation_status: escalationStatus || undefined,
  });
  const scan = useScanAnomalies();
  const explain = useExplainAnomalies();
  const updateStatus = useUpdateAnomalyStatus();

  const [lastScan, setLastScan] = useState<string | null>(null);
  const [explainMsg, setExplainMsg] = useState<string | null>(null);

  const onScan = async () => {
    const res = await scan.mutateAsync();
    setLastScan(
      `Scanned: ${res.total_detected} anomalies (${res.new} new, ${res.updated} refreshed)`,
    );
  };

  const onExplain = async () => {
    setExplainMsg(null);
    const res = await explain.mutateAsync(20);
    if (res.skipped_reason) {
      setExplainMsg(`LLM skipped: ${res.skipped_reason}`);
    } else if (res.attempted === 0) {
      setExplainMsg("All anomalies already explained.");
    } else {
      setExplainMsg(`Explained ${res.explained}/${res.attempted} anomalies.`);
    }
  };

  const onAck = (id: number, nextStatus: AnomalyStatus) =>
    updateStatus.mutateAsync({ id, status: nextStatus, acknowledgedBy: "demo-user" });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div className="flex flex-wrap items-end gap-3 text-xs">
          <Filter label="Severity" value={severity} onChange={setSeverity}>
            <option value="">All</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </Filter>
          <Filter label="Status" value={status} onChange={setStatus}>
            <option value="">All</option>
            <option value="new">New</option>
            <option value="acknowledged">Acknowledged</option>
            <option value="dismissed">Dismissed</option>
            <option value="resolved">Resolved</option>
          </Filter>
          <Filter label="Detector" value={detector} onChange={setDetector}>
            <option value="">All</option>
            <option value="outlier_zscore">z-score outlier</option>
            <option value="period_gap">missing period</option>
            <option value="zero_value">zero-value report</option>
            <option value="spike_pct">sudden spike</option>
          </Filter>
          <Filter label="Escalation" value={escalationStatus} onChange={setEscalationStatus}>
            <option value="">All</option>
            <option value="any">Escalated (any)</option>
            <option value="escalated">Awaiting board</option>
            <option value="board_reviewed">Board-reviewed</option>
          </Filter>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={onScan} disabled={scan.isPending}>
            {scan.isPending ? "Scanning…" : "Run scan"}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={onExplain}
            disabled={explain.isPending}
            title="Generate plain-English explanations for anomalies that don't have one yet."
          >
            <Sparkles size={12} />
            {explain.isPending ? "Explaining…" : "Explain with AI"}
          </Button>
        </div>
      </div>

      {(lastScan || explainMsg) && (
        <div className="flex flex-col gap-1 text-xs text-slate-500">
          {lastScan && <div>{lastScan}</div>}
          {explainMsg && <div>{explainMsg}</div>}
        </div>
      )}

      {list.isLoading && <LoadingState label="Loading anomaly feed…" />}
      {list.isError && <ErrorState error={list.error} />}

      {list.data && list.data.length === 0 && (
        <div className="rounded-md border border-dashed border-slate-200 p-10 text-center text-sm text-slate-400">
          No anomalies match these filters. Try Run scan to refresh.
        </div>
      )}

      {list.data && list.data.length > 0 && (
        <div className="space-y-3">
          {list.data.map((a) => (
            <AnomalyCard key={a.id} anomaly={a} onStatusChange={onAck} />
          ))}
        </div>
      )}
    </div>
  );
}

function AnomalyCard({
  anomaly,
  onStatusChange,
}: {
  anomaly: Anomaly;
  onStatusChange: (id: number, s: AnomalyStatus) => Promise<unknown>;
}) {
  return (
    <div
      className={`rounded-md border border-slate-200 border-l-4 p-4 ${SEVERITY_STYLES[anomaly.severity]}`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <AlertTriangle
            size={18}
            className={
              anomaly.severity === "critical" || anomaly.severity === "high"
                ? "mt-0.5 text-red-600"
                : "mt-0.5 text-amber-600"
            }
          />
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span
                className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${SEVERITY_BADGE[anomaly.severity]}`}
              >
                {anomaly.severity}
              </span>
              <span className="rounded-full bg-slate-200/60 px-2 py-0.5 text-[10px] font-medium uppercase text-slate-600">
                {DETECTOR_LABEL[anomaly.detector]}
              </span>
              <span
                className={`rounded-full px-2 py-0.5 text-[10px] font-medium uppercase ${STATUS_BADGE[anomaly.status]}`}
              >
                {anomaly.status}
              </span>
              {anomaly.escalation_status === "escalated" && (
                <span className="inline-flex items-center gap-1 rounded-full bg-violet-100 px-2 py-0.5 text-[10px] font-medium uppercase text-violet-700">
                  <ShieldAlert size={10} />
                  Escalated
                </span>
              )}
              {anomaly.escalation_status === "board_reviewed" && (
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-medium uppercase text-emerald-700">
                  <Gavel size={10} />
                  Board-reviewed
                </span>
              )}
            </div>
            <h4 className="text-sm font-semibold text-slate-900">{anomaly.title}</h4>
            <p className="text-xs text-slate-600">{anomaly.description}</p>
          </div>
        </div>
        {anomaly.status === "new" && (
          <div className="flex shrink-0 gap-1">
            <button
              type="button"
              onClick={() => onStatusChange(anomaly.id, "acknowledged")}
              className="flex items-center gap-1 rounded border border-blue-200 bg-blue-50 px-2 py-1 text-[10px] text-blue-700 hover:bg-blue-100"
              title="Acknowledge — I've seen this"
            >
              <Check size={10} />
              Ack
            </button>
            <button
              type="button"
              onClick={() => onStatusChange(anomaly.id, "dismissed")}
              className="flex items-center gap-1 rounded border border-slate-200 bg-white px-2 py-1 text-[10px] text-slate-600 hover:bg-slate-50"
              title="Dismiss — false positive"
            >
              <X size={10} />
              Dismiss
            </button>
          </div>
        )}
      </div>

      {anomaly.llm_explanation && (
        <div className="mt-3 rounded-md bg-white/60 p-3 text-xs text-slate-700 ring-1 ring-inset ring-slate-200">
          <div className="mb-1 flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
            <Sparkles size={10} />
            AI analyst note
          </div>
          {anomaly.llm_explanation}
        </div>
      )}

      <EscalationPanel anomaly={anomaly} />

      {anomaly.z_score !== null && (
        <div className="mt-2 flex gap-4 text-[11px] text-slate-500">
          <span>
            Observed:{" "}
            <span className="font-mono font-medium text-slate-700">
              {anomaly.metric_value?.toLocaleString()}
            </span>
          </span>
          {anomaly.expected_value !== null && (
            <span>
              Expected ~
              <span className="font-mono font-medium text-slate-700">
                {anomaly.expected_value.toLocaleString(undefined, {
                  maximumFractionDigits: 1,
                })}
              </span>
            </span>
          )}
          <span>
            z = <span className="font-mono font-medium text-slate-700">{anomaly.z_score.toFixed(1)}</span>
          </span>
        </div>
      )}
    </div>
  );
}

function Filter({
  label,
  value,
  onChange,
  children,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  children: React.ReactNode;
}) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-slate-500">{label}</span>
      <select
        className="rounded-md border border-slate-200 bg-white px-2 py-1 text-xs focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {children}
      </select>
    </label>
  );
}
