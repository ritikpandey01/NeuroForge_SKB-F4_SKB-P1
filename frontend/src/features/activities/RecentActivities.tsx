import { Trash2 } from "lucide-react";
import { useState } from "react";

import { ErrorState, LoadingState } from "@/components/common/LoadingState";
import { Button } from "@/components/ui/button";

import { useActivities, useDeleteActivity, useFacilities } from "./api";

export function RecentActivities() {
  const [facilityFilter, setFacilityFilter] = useState<number | undefined>(undefined);
  const [scopeFilter, setScopeFilter] = useState<number | undefined>(undefined);
  const facilities = useFacilities();
  const list = useActivities({
    facility_id: facilityFilter,
    scope: scopeFilter,
    limit: 50,
  });
  const del = useDeleteActivity();

  const onDelete = async (id: number) => {
    if (!confirm(`Delete activity #${id}? This also removes its emissions row.`)) return;
    await del.mutateAsync(id);
  };

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-3 text-xs">
        <label className="flex items-center gap-2">
          <span className="text-slate-500">Facility:</span>
          <select
            className="rounded-md border border-slate-200 bg-white px-2 py-1"
            value={facilityFilter ?? ""}
            onChange={(e) =>
              setFacilityFilter(e.target.value ? Number(e.target.value) : undefined)
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
        <label className="flex items-center gap-2">
          <span className="text-slate-500">Scope:</span>
          <select
            className="rounded-md border border-slate-200 bg-white px-2 py-1"
            value={scopeFilter ?? ""}
            onChange={(e) =>
              setScopeFilter(e.target.value ? Number(e.target.value) : undefined)
            }
          >
            <option value="">All</option>
            <option value="1">Scope 1</option>
            <option value="2">Scope 2</option>
            <option value="3">Scope 3</option>
          </select>
        </label>
        <span className="text-slate-400">
          Showing latest 50 rows · {list.data?.length ?? 0} loaded
        </span>
      </div>

      {list.isLoading && <LoadingState label="Loading activity data…" />}
      {list.isError && <ErrorState error={list.error} />}

      {list.data && (
        <div className="overflow-x-auto rounded-md border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200 text-xs">
            <thead className="bg-slate-50 text-slate-500">
              <tr>
                <Th>ID</Th>
                <Th>Period</Th>
                <Th>Facility</Th>
                <Th>Scope</Th>
                <Th>Subcategory</Th>
                <Th className="text-right">Quantity</Th>
                <Th>Unit</Th>
                <Th>Source</Th>
                <Th>DQ</Th>
                <Th />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {list.data.map((a) => (
                <tr key={a.id} className="hover:bg-slate-50/50">
                  <Td>#{a.id}</Td>
                  <Td className="whitespace-nowrap">
                    {a.period_start} → {a.period_end}
                  </Td>
                  <Td>{a.facility_name}</Td>
                  <Td>{a.scope}</Td>
                  <Td className="font-mono">{a.subcategory}</Td>
                  <Td className="text-right font-mono">{a.quantity.toLocaleString()}</Td>
                  <Td>{a.unit}</Td>
                  <Td className="max-w-[200px] text-slate-500">
                    <span title={a.source_document ?? ""} className="block truncate">
                      {a.source_document ?? "—"}
                    </span>
                  </Td>
                  <Td>{a.data_quality_score}</Td>
                  <Td>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => onDelete(a.id)}
                      title="Delete"
                    >
                      <Trash2 size={14} />
                    </Button>
                  </Td>
                </tr>
              ))}
              {list.data.length === 0 && (
                <tr>
                  <td colSpan={10} className="p-6 text-center text-slate-400">
                    No activity rows match these filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function Th({ children, className }: { children?: React.ReactNode; className?: string }) {
  return (
    <th
      className={`px-3 py-2 text-left text-[10px] font-semibold uppercase tracking-wide ${className ?? ""}`}
    >
      {children}
    </th>
  );
}

function Td({ children, className }: { children: React.ReactNode; className?: string }) {
  return <td className={`px-3 py-1.5 align-top text-slate-700 ${className ?? ""}`}>{children}</td>;
}
