import { useMemo, useState } from "react";

import { ErrorState, LoadingState } from "@/components/common/LoadingState";
import { Button } from "@/components/ui/button";

import {
  useAllSubmissions,
  useCreateSubmission,
  useSuppliers,
  useUpdateSubmissionStatus,
} from "./api";
import type { SubmissionStatus } from "./types";

const STATUS_STYLES: Record<SubmissionStatus, string> = {
  pending: "bg-slate-100 text-slate-700",
  accepted: "bg-emerald-50 text-emerald-700",
  flagged: "bg-amber-50 text-amber-800",
  rejected: "bg-red-50 text-red-700",
};

const METHODOLOGIES = [
  { value: "primary_activity_data", label: "Primary activity data" },
  { value: "supplier_specific", label: "Supplier-specific factor" },
  { value: "spend_based_eeio", label: "Spend-based (EEIO)" },
];

export function SubmissionForm() {
  const suppliers = useSuppliers();
  const submissions = useAllSubmissions();
  const create = useCreateSubmission();
  const updateStatus = useUpdateSubmissionStatus();

  const [supplierId, setSupplierId] = useState<number>(0);
  const [period, setPeriod] = useState("2024-Q4");
  const [emissions, setEmissions] = useState("");
  const [methodology, setMethodology] = useState("supplier_specific");
  const [notes, setNotes] = useState("");
  const [dq, setDq] = useState(3);
  const [okMessage, setOkMessage] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const supplierById = useMemo(() => {
    const map = new Map<number, string>();
    (suppliers.data ?? []).forEach((s) => map.set(s.id, s.name));
    return map;
  }, [suppliers.data]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setOkMessage(null);
    setErrorMsg(null);

    if (!supplierId) {
      setErrorMsg("Pick a supplier first.");
      return;
    }

    const supplier = (suppliers.data ?? []).find((s) => s.id === supplierId);
    if (!supplier) return;

    try {
      const created = await create.mutateAsync({
        supplierId,
        payload: {
          period,
          data_quality_score: dq,
          submitted_data: {
            total_emissions_tco2e: Number(emissions),
            scope: 3,
            scope3_category: supplier.scope3_category,
            methodology,
            notes: notes || null,
          },
        },
      });
      setOkMessage(`Submission #${created.id} recorded — awaiting review.`);
      setEmissions("");
      setNotes("");
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : String(err));
    }
  };

  const onStatusChange = async (id: number, status: SubmissionStatus) => {
    try {
      await updateStatus.mutateAsync({ id, status });
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : String(err));
    }
  };

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_1.2fr]">
      {/* Submit form — portal-facing side */}
      <form onSubmit={onSubmit} className="space-y-4">
        <p className="text-xs text-slate-500">
          Supplier reports one quarter of emissions at a time. All submissions start as{" "}
          <span className="font-medium">pending</span> and require internal review before they
          contribute to the org roll-up.
        </p>

        <div className="grid grid-cols-1 gap-3">
          <Field label="Supplier">
            <select
              required
              className={inputCls}
              value={supplierId}
              onChange={(e) => setSupplierId(Number(e.target.value))}
            >
              <option value={0} disabled>
                Select supplier…
              </option>
              {(suppliers.data ?? []).map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} · {s.industry}
                </option>
              ))}
            </select>
          </Field>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Reporting period">
              <input
                required
                className={inputCls}
                placeholder="2024-Q4"
                value={period}
                onChange={(e) => setPeriod(e.target.value)}
              />
            </Field>
            <Field label="Data quality (1–5)">
              <input
                type="number"
                min={1}
                max={5}
                className={inputCls}
                value={dq}
                onChange={(e) => setDq(Number(e.target.value))}
              />
            </Field>
          </div>

          <Field label="Total reported emissions (tCO₂e)">
            <input
              required
              type="number"
              step="any"
              min={0}
              className={inputCls}
              value={emissions}
              onChange={(e) => setEmissions(e.target.value)}
            />
          </Field>

          <Field label="Methodology">
            <select
              className={inputCls}
              value={methodology}
              onChange={(e) => setMethodology(e.target.value)}
            >
              {METHODOLOGIES.map((m) => (
                <option key={m.value} value={m.value}>
                  {m.label}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Notes (optional)">
            <textarea
              rows={2}
              className={inputCls}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </Field>
        </div>

        <div className="flex items-center gap-3">
          <Button type="submit" disabled={create.isPending}>
            {create.isPending ? "Submitting…" : "Submit quarter"}
          </Button>
          {okMessage && <span className="text-xs text-emerald-700">{okMessage}</span>}
          {errorMsg && <span className="text-xs text-danger">Failed: {errorMsg}</span>}
        </div>
      </form>

      {/* Review queue — ESG team side */}
      <div className="space-y-3">
        <h4 className="text-sm font-semibold text-slate-700">Review queue</h4>
        {submissions.isLoading && <LoadingState label="Loading submissions…" />}
        {submissions.isError && <ErrorState error={submissions.error} />}
        {submissions.data && (
          <div className="max-h-[480px] overflow-y-auto rounded-md border border-slate-200">
            <table className="min-w-full divide-y divide-slate-200 text-xs">
              <thead className="sticky top-0 bg-slate-50 text-slate-500">
                <tr>
                  <Th>Supplier</Th>
                  <Th>Period</Th>
                  <Th className="text-right">tCO₂e</Th>
                  <Th>DQ</Th>
                  <Th>Status</Th>
                  <Th>Actions</Th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {submissions.data.map((s) => {
                  const emissions =
                    typeof s.submitted_data?.total_emissions_tco2e === "number"
                      ? (s.submitted_data.total_emissions_tco2e as number)
                      : null;
                  return (
                    <tr key={s.id} className="hover:bg-slate-50/50">
                      <Td className="font-medium text-slate-800">
                        {s.supplier_name ?? supplierById.get(s.supplier_id) ?? `#${s.supplier_id}`}
                      </Td>
                      <Td>{s.period}</Td>
                      <Td className="text-right font-mono">
                        {emissions !== null
                          ? emissions.toLocaleString("en-IN", { maximumFractionDigits: 1 })
                          : "—"}
                      </Td>
                      <Td>{s.data_quality_score}</Td>
                      <Td>
                        <span
                          className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-medium uppercase ${
                            STATUS_STYLES[s.status]
                          }`}
                        >
                          {s.status}
                        </span>
                      </Td>
                      <Td>
                        {s.status === "pending" ? (
                          <div className="flex gap-1">
                            <button
                              type="button"
                              onClick={() => onStatusChange(s.id, "accepted")}
                              className="rounded border border-emerald-200 bg-emerald-50 px-2 py-0.5 text-[10px] text-emerald-700 hover:bg-emerald-100"
                            >
                              Accept
                            </button>
                            <button
                              type="button"
                              onClick={() => onStatusChange(s.id, "flagged")}
                              className="rounded border border-amber-200 bg-amber-50 px-2 py-0.5 text-[10px] text-amber-800 hover:bg-amber-100"
                            >
                              Flag
                            </button>
                            <button
                              type="button"
                              onClick={() => onStatusChange(s.id, "rejected")}
                              className="rounded border border-red-200 bg-red-50 px-2 py-0.5 text-[10px] text-red-700 hover:bg-red-100"
                            >
                              Reject
                            </button>
                          </div>
                        ) : (
                          <span className="text-slate-400">—</span>
                        )}
                      </Td>
                    </tr>
                  );
                })}
                {submissions.data.length === 0 && (
                  <tr>
                    <td colSpan={6} className="p-6 text-center text-slate-400">
                      No submissions yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

const inputCls =
  "w-full rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand";

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-xs font-medium text-slate-600">{label}</span>
      {children}
    </label>
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
  return (
    <td className={`px-3 py-1.5 align-top text-slate-700 ${className ?? ""}`}>{children}</td>
  );
}
