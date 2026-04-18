import { useMemo, useState } from "react";

import { ErrorState, LoadingState } from "@/components/common/LoadingState";

import { useSuppliers } from "./api";
import type { MaturityLevel, Supplier, SubmissionStatus } from "./types";

const MATURITY_LABELS: Record<MaturityLevel, string> = {
  spend_based: "Spend-based",
  activity_based: "Activity-based",
  verified_primary: "Verified primary",
};

const STATUS_STYLES: Record<SubmissionStatus, string> = {
  pending: "bg-slate-100 text-slate-600",
  accepted: "bg-emerald-50 text-emerald-700",
  flagged: "bg-amber-50 text-amber-800",
  rejected: "bg-red-50 text-red-700",
};

export function SupplierRegistry() {
  const [search, setSearch] = useState("");
  const [industry, setIndustry] = useState<string>("");
  const [tier, setTier] = useState<number | "">("");
  const [maturity, setMaturity] = useState<string>("");

  const list = useSuppliers({
    search: search || undefined,
    industry: industry || undefined,
    tier: tier === "" ? undefined : tier,
    data_maturity_level: maturity || undefined,
  });

  const industries = useMemo(() => {
    const seen = new Set<string>();
    (list.data ?? []).forEach((s) => seen.add(s.industry));
    return Array.from(seen).sort();
  }, [list.data]);

  const totalSpend = useMemo(
    () => (list.data ?? []).reduce((sum, s) => sum + s.annual_spend, 0),
    [list.data],
  );

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end gap-3 text-xs">
        <label className="flex flex-col gap-1">
          <span className="text-slate-500">Search name</span>
          <input
            className={inputCls}
            placeholder="SteelCorp…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-slate-500">Industry</span>
          <select
            className={inputCls}
            value={industry}
            onChange={(e) => setIndustry(e.target.value)}
          >
            <option value="">All</option>
            {industries.map((i) => (
              <option key={i} value={i}>
                {i}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-slate-500">Tier</span>
          <select
            className={inputCls}
            value={tier}
            onChange={(e) => setTier(e.target.value === "" ? "" : Number(e.target.value))}
          >
            <option value="">All</option>
            <option value={1}>Tier 1</option>
            <option value={2}>Tier 2</option>
            <option value={3}>Tier 3</option>
          </select>
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-slate-500">Data maturity</span>
          <select
            className={inputCls}
            value={maturity}
            onChange={(e) => setMaturity(e.target.value)}
          >
            <option value="">All</option>
            <option value="spend_based">Spend-based</option>
            <option value="activity_based">Activity-based</option>
            <option value="verified_primary">Verified primary</option>
          </select>
        </label>
        <span className="ml-auto text-slate-500">
          {list.data?.length ?? 0} suppliers · ₹
          {totalSpend.toLocaleString("en-IN", { maximumFractionDigits: 1 })} Cr total spend
        </span>
      </div>

      {list.isLoading && <LoadingState label="Loading suppliers…" />}
      {list.isError && <ErrorState error={list.error} />}

      {list.data && (
        <div className="overflow-x-auto rounded-md border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200 text-xs">
            <thead className="bg-slate-50 text-slate-500">
              <tr>
                <Th>Name</Th>
                <Th>Industry</Th>
                <Th>Tier</Th>
                <Th>Data maturity</Th>
                <Th>Scope 3 category</Th>
                <Th className="text-right">Annual spend (₹ Cr)</Th>
                <Th className="text-right">Submissions</Th>
                <Th>Latest</Th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {list.data.map((s: Supplier) => (
                <tr key={s.id} className="hover:bg-slate-50/50">
                  <Td className="font-medium text-slate-800">{s.name}</Td>
                  <Td>{s.industry}</Td>
                  <Td>T{s.tier}</Td>
                  <Td>{MATURITY_LABELS[s.data_maturity_level]}</Td>
                  <Td className="font-mono text-[11px] text-slate-500">
                    {s.scope3_category}
                  </Td>
                  <Td className="text-right font-mono">
                    {s.annual_spend.toLocaleString("en-IN", {
                      minimumFractionDigits: 1,
                      maximumFractionDigits: 1,
                    })}
                  </Td>
                  <Td className="text-right">{s.submissions_count}</Td>
                  <Td>
                    {s.latest_submission_status ? (
                      <span
                        className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-medium uppercase ${
                          STATUS_STYLES[s.latest_submission_status]
                        }`}
                      >
                        {s.latest_submission_status}
                      </span>
                    ) : (
                      <span className="text-slate-400">—</span>
                    )}
                  </Td>
                </tr>
              ))}
              {list.data.length === 0 && (
                <tr>
                  <td colSpan={8} className="p-6 text-center text-slate-400">
                    No suppliers match these filters.
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

const inputCls =
  "rounded-md border border-slate-200 bg-white px-2 py-1 text-xs focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand";

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
  return (
    <td className={`px-3 py-1.5 align-top text-slate-700 ${className ?? ""}`}>
      {children}
    </td>
  );
}
