import { ChevronDown, ChevronRight } from "lucide-react";
import { Fragment, useState } from "react";

import { Button } from "@/components/ui/button";
import { ErrorState, LoadingState } from "@/components/common/LoadingState";

import { useAuditLog } from "./api";
import type { AuditEntry, AuditFilters } from "./types";

const ACTION_STYLES: Record<string, string> = {
  create: "bg-emerald-50 text-emerald-700",
  update: "bg-sky-50 text-sky-700",
  delete: "bg-red-50 text-red-700",
  review: "bg-indigo-50 text-indigo-700",
  generate: "bg-violet-50 text-violet-700",
  acknowledge: "bg-amber-50 text-amber-800",
  dismissed: "bg-slate-100 text-slate-600",
  resolved: "bg-emerald-50 text-emerald-700",
  bulk_create: "bg-teal-50 text-teal-700",
};

function prettyJSON(raw: string | null): string {
  if (!raw) return "—";
  try {
    return JSON.stringify(JSON.parse(raw), null, 2);
  } catch {
    return raw;
  }
}

function DiffBlock({ label, raw }: { label: string; raw: string | null }) {
  return (
    <div className="flex-1 min-w-0">
      <div className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
        {label}
      </div>
      <pre className="max-h-48 overflow-auto rounded-md border border-slate-200 bg-slate-50 p-2 text-[11px] leading-relaxed text-slate-800">
        {prettyJSON(raw)}
      </pre>
    </div>
  );
}

function Row({ entry }: { entry: AuditEntry }) {
  const [open, setOpen] = useState(false);
  const expandable = entry.old_value || entry.new_value;

  return (
    <Fragment>
      <tr
        className={`border-t border-slate-100 ${expandable ? "cursor-pointer hover:bg-slate-50/60" : ""}`}
        onClick={() => expandable && setOpen((v) => !v)}
      >
        <td className="w-6 px-2 py-2 text-slate-400">
          {expandable ? (
            open ? (
              <ChevronDown size={14} />
            ) : (
              <ChevronRight size={14} />
            )
          ) : null}
        </td>
        <td className="px-3 py-2 text-xs text-slate-500 whitespace-nowrap">
          {new Date(entry.timestamp).toLocaleString()}
        </td>
        <td className="px-3 py-2 text-xs">
          <span
            className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${
              ACTION_STYLES[entry.action] ?? "bg-slate-100 text-slate-600"
            }`}
          >
            {entry.action}
          </span>
        </td>
        <td className="px-3 py-2 font-mono text-xs text-slate-700">
          {entry.entity_type}
          {entry.entity_id > 0 ? `#${entry.entity_id}` : ""}
        </td>
        <td className="px-3 py-2 text-xs text-slate-600">{entry.user}</td>
      </tr>
      {open && expandable && (
        <tr className="bg-slate-50/40">
          <td colSpan={5} className="px-6 py-3">
            <div className="flex flex-col gap-3 md:flex-row">
              <DiffBlock label="Before" raw={entry.old_value} />
              <DiffBlock label="After" raw={entry.new_value} />
            </div>
          </td>
        </tr>
      )}
    </Fragment>
  );
}

type Props = {
  filters: AuditFilters;
  onChangeFilters: (f: AuditFilters) => void;
};

export function AuditTable({ filters, onChangeFilters }: Props) {
  const q = useAuditLog(filters);

  if (q.isLoading && !q.data) return <LoadingState label="Loading audit log…" />;
  if (q.isError) return <ErrorState error={q.error} />;
  if (!q.data) return null;

  const { total, limit, offset, entries } = q.data;
  const page = Math.floor(offset / limit) + 1;
  const pages = Math.max(1, Math.ceil(total / limit));

  return (
    <div className="space-y-3">
      <div className="overflow-hidden rounded-md border border-slate-200">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-[10px] uppercase tracking-widest text-slate-500">
            <tr>
              <th className="w-6 px-2 py-2"></th>
              <th className="px-3 py-2 text-left">Timestamp</th>
              <th className="px-3 py-2 text-left">Action</th>
              <th className="px-3 py-2 text-left">Entity</th>
              <th className="px-3 py-2 text-left">User</th>
            </tr>
          </thead>
          <tbody>
            {entries.length === 0 ? (
              <tr>
                <td
                  colSpan={5}
                  className="px-6 py-12 text-center text-sm text-slate-400"
                >
                  No audit entries match these filters.
                </td>
              </tr>
            ) : (
              entries.map((e) => <Row key={e.id} entry={e} />)
            )}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between text-xs text-slate-500">
        <div>
          {total === 0
            ? "0 entries"
            : `Showing ${offset + 1}–${Math.min(offset + entries.length, total)} of ${total}`}
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={offset === 0}
            onClick={() =>
              onChangeFilters({
                ...filters,
                offset: Math.max(0, offset - limit),
              })
            }
          >
            Prev
          </Button>
          <span className="font-mono">
            {page} / {pages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={offset + limit >= total}
            onClick={() =>
              onChangeFilters({ ...filters, offset: offset + limit })
            }
          >
            Next
          </Button>
        </div>
      </div>
    </div>
  );
}
