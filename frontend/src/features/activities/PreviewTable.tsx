import { useMemo } from "react";

import { Button } from "@/components/ui/button";

import type { CsvPreviewResponse, CsvPreviewRow } from "./types";

type Props = {
  preview: CsvPreviewResponse;
  onCommit: (rows: NonNullable<CsvPreviewRow["parsed"]>[]) => void;
  committing: boolean;
};

export function PreviewTable({ preview, onCommit, committing }: Props) {
  const readyRows = useMemo(
    () =>
      preview.rows
        .filter((r) => r.parsed && !r.issues.some((i) => i.severity === "error"))
        .map((r) => r.parsed!),
    [preview],
  );

  if (preview.summary.error) {
    return (
      <div className="rounded-md border border-danger/30 bg-red-50 p-3 text-xs text-danger">
        {preview.summary.error}
        {preview.summary.required && (
          <div className="mt-1 text-slate-600">
            Required: {preview.summary.required.join(", ")}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {preview.document_summary && (
        <div className="rounded-md border border-brand/20 bg-brand/5 p-3 text-xs text-slate-700">
          <span className="font-semibold text-brand">AI summary:</span>{" "}
          {preview.document_summary}
        </div>
      )}

      {preview.model_warnings && preview.model_warnings.length > 0 && (
        <div className="rounded-md border border-amber-300 bg-amber-50 p-3 text-xs text-amber-800">
          <div className="font-semibold">Document-level notes from the parser:</div>
          <ul className="mt-1 list-disc space-y-0.5 pl-5">
            {preview.model_warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-4 text-xs">
        <Stat label="Total" value={preview.summary.total_rows ?? 0} />
        <Stat label="Ready" value={preview.summary.rows_ready ?? 0} tone="ok" />
        <Stat
          label="Warnings"
          value={preview.summary.rows_with_warnings ?? 0}
          tone="warn"
        />
        <Stat
          label="Errors"
          value={preview.summary.rows_with_errors ?? 0}
          tone="error"
        />
        <div className="flex-1" />
        <Button
          onClick={() => onCommit(readyRows)}
          disabled={!readyRows.length || committing}
        >
          {committing
            ? "Committing…"
            : `Commit ${readyRows.length} ready row${readyRows.length === 1 ? "" : "s"}`}
        </Button>
      </div>

      <div className="overflow-x-auto rounded-md border border-slate-200">
        <table className="min-w-full divide-y divide-slate-200 text-xs">
          <thead className="bg-slate-50 text-slate-500">
            <tr>
              <Th>#</Th>
              <Th>Status</Th>
              <Th>Facility</Th>
              <Th>Scope</Th>
              <Th>Subcategory</Th>
              <Th className="text-right">Quantity</Th>
              <Th>Unit</Th>
              <Th>Period</Th>
              <Th>Notes</Th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {preview.rows.map((r) => {
              const hasError = r.issues.some((i) => i.severity === "error");
              const hasWarn = r.issues.some((i) => i.severity === "warning");
              const facility = String(
                r.parsed?.facility_id != null
                  ? r.raw.facility_name ?? "—"
                  : r.raw.facility_name ?? "—",
              );
              const period =
                r.parsed?.period_start && r.parsed?.period_end
                  ? `${r.parsed.period_start} → ${r.parsed.period_end}`
                  : `${r.raw.period_start ?? ""} → ${r.raw.period_end ?? ""}`;
              return (
                <tr
                  key={r.row_number}
                  className={
                    hasError
                      ? "bg-red-50/40"
                      : hasWarn
                        ? "bg-amber-50/40"
                        : ""
                  }
                >
                  <Td>{r.row_number}</Td>
                  <Td>
                    <StatusPill error={hasError} warn={hasWarn} />
                  </Td>
                  <Td>{facility}</Td>
                  <Td>{String(r.raw.scope ?? r.parsed?.scope ?? "")}</Td>
                  <Td className="font-mono">
                    {String(r.raw.subcategory ?? r.parsed?.subcategory ?? "")}
                  </Td>
                  <Td className="text-right font-mono">
                    {String(r.raw.quantity ?? r.parsed?.quantity ?? "")}
                  </Td>
                  <Td>{String(r.raw.unit ?? r.parsed?.unit ?? "")}</Td>
                  <Td className="whitespace-nowrap">{period}</Td>
                  <Td>
                    {r.issues.length === 0 ? (
                      <span className="text-slate-400">—</span>
                    ) : (
                      <ul className="space-y-0.5">
                        {r.issues.map((i, idx) => (
                          <li key={idx} className={severityClass(i.severity)}>
                            {i.message}
                          </li>
                        ))}
                      </ul>
                    )}
                  </Td>
                </tr>
              );
            })}
            {preview.rows.length === 0 && (
              <tr>
                <td colSpan={9} className="p-6 text-center text-slate-400">
                  No rows extracted.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function severityClass(s: "error" | "warning" | "info"): string {
  if (s === "error") return "text-danger";
  if (s === "warning") return "text-amber-700";
  return "text-slate-500";
}

function Stat({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone?: "ok" | "warn" | "error";
}) {
  const color =
    tone === "ok"
      ? "text-emerald-700"
      : tone === "warn"
        ? "text-amber-700"
        : tone === "error"
          ? "text-danger"
          : "text-slate-700";
  return (
    <span className="flex items-baseline gap-1">
      <span className="text-slate-500">{label}:</span>
      <span className={`font-semibold ${color}`}>{value}</span>
    </span>
  );
}

function StatusPill({ error, warn }: { error: boolean; warn: boolean }) {
  if (error)
    return <span className="rounded-full bg-red-100 px-2 py-0.5 text-danger">error</span>;
  if (warn)
    return (
      <span className="rounded-full bg-amber-100 px-2 py-0.5 text-amber-700">warn</span>
    );
  return (
    <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-emerald-700">ready</span>
  );
}

function Th({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <th
      className={`px-3 py-2 text-left text-[10px] font-semibold uppercase tracking-wide ${className ?? ""}`}
    >
      {children}
    </th>
  );
}

function Td({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <td className={`px-3 py-1.5 align-top text-slate-700 ${className ?? ""}`}>{children}</td>
  );
}
