import { Search, X } from "lucide-react";

import { Button } from "@/components/ui/button";

import { useAuditFilterOptions } from "./api";
import type { AuditFilters as AuditFiltersT } from "./types";

type Props = {
  value: AuditFiltersT;
  onChange: (next: AuditFiltersT) => void;
};

export function AuditFilters({ value, onChange }: Props) {
  const opts = useAuditFilterOptions();

  const set = (patch: Partial<AuditFiltersT>) =>
    onChange({ ...value, ...patch, offset: 0 });

  const clear = () =>
    onChange({
      limit: value.limit,
      offset: 0,
    });

  const anyActive =
    value.entity_type ||
    value.action ||
    value.user ||
    value.from ||
    value.to ||
    value.q;

  return (
    <div className="rounded-md border border-slate-200 bg-white p-3">
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-6">
        <div>
          <label className="block text-[10px] uppercase tracking-wider text-slate-500">
            Entity
          </label>
          <select
            value={value.entity_type ?? ""}
            onChange={(e) =>
              set({ entity_type: e.target.value || undefined })
            }
            className="mt-1 h-8 w-full rounded-md border border-slate-300 bg-white px-2 text-xs"
          >
            <option value="">All</option>
            {opts.data?.entity_types.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-[10px] uppercase tracking-wider text-slate-500">
            Action
          </label>
          <select
            value={value.action ?? ""}
            onChange={(e) => set({ action: e.target.value || undefined })}
            className="mt-1 h-8 w-full rounded-md border border-slate-300 bg-white px-2 text-xs"
          >
            <option value="">All</option>
            {opts.data?.actions.map((a) => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-[10px] uppercase tracking-wider text-slate-500">
            User
          </label>
          <select
            value={value.user ?? ""}
            onChange={(e) => set({ user: e.target.value || undefined })}
            className="mt-1 h-8 w-full rounded-md border border-slate-300 bg-white px-2 text-xs"
          >
            <option value="">All</option>
            {opts.data?.users.map((u) => (
              <option key={u} value={u}>
                {u}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-[10px] uppercase tracking-wider text-slate-500">
            From
          </label>
          <input
            type="date"
            value={value.from ?? ""}
            onChange={(e) => set({ from: e.target.value || undefined })}
            className="mt-1 h-8 w-full rounded-md border border-slate-300 bg-white px-2 text-xs"
          />
        </div>

        <div>
          <label className="block text-[10px] uppercase tracking-wider text-slate-500">
            To
          </label>
          <input
            type="date"
            value={value.to ?? ""}
            onChange={(e) => set({ to: e.target.value || undefined })}
            className="mt-1 h-8 w-full rounded-md border border-slate-300 bg-white px-2 text-xs"
          />
        </div>

        <div>
          <label className="block text-[10px] uppercase tracking-wider text-slate-500">
            Search
          </label>
          <div className="relative mt-1">
            <Search
              size={12}
              className="absolute left-2 top-1/2 -translate-y-1/2 text-slate-400"
            />
            <input
              type="text"
              placeholder="json / user / type"
              value={value.q ?? ""}
              onChange={(e) => set({ q: e.target.value || undefined })}
              className="h-8 w-full rounded-md border border-slate-300 bg-white pl-7 pr-2 text-xs"
            />
          </div>
        </div>
      </div>

      {anyActive ? (
        <div className="mt-3 flex justify-end">
          <Button variant="outline" size="sm" onClick={clear}>
            <X size={12} />
            Clear filters
          </Button>
        </div>
      ) : null}
    </div>
  );
}
