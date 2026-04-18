import { useState } from "react";

import { Button } from "@/components/ui/button";

import { useCreateActivity, useFacilities } from "./api";
import type { ValidationIssue } from "./types";

const SCOPE_OPTIONS = [
  { value: 1, label: "Scope 1 — Direct" },
  { value: 2, label: "Scope 2 — Electricity" },
  { value: 3, label: "Scope 3 — Value chain" },
];

const QUICK_TEMPLATES: Record<
  number,
  { category: string; subcategory: string; unit: string }[]
> = {
  1: [
    { category: "fuel", subcategory: "diesel", unit: "litres" },
    { category: "fuel", subcategory: "natural_gas", unit: "m3" },
    { category: "refrigerant", subcategory: "r410a", unit: "kg" },
  ],
  2: [{ category: "electricity", subcategory: "grid_india", unit: "kWh" }],
  3: [
    { category: "material", subcategory: "steel", unit: "kg" },
    { category: "freight", subcategory: "road_hgv", unit: "tonne-km" },
    { category: "travel", subcategory: "flight_short_haul", unit: "passenger-km" },
    { category: "commute", subcategory: "car_petrol", unit: "km" },
  ],
};

export function ManualEntryForm() {
  const facilities = useFacilities();
  const create = useCreateActivity();

  const [form, setForm] = useState({
    facility_id: 0,
    scope: 2,
    category: "electricity",
    subcategory: "grid_india",
    activity_description: "",
    quantity: "",
    unit: "kWh",
    period_start: "",
    period_end: "",
    data_quality_score: 3,
  });
  const [issues, setIssues] = useState<ValidationIssue[]>([]);
  const [okMessage, setOkMessage] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const update = <K extends keyof typeof form>(k: K, v: (typeof form)[K]) =>
    setForm((f) => ({ ...f, [k]: v }));

  const applyTemplate = (t: { category: string; subcategory: string; unit: string }) => {
    setForm((f) => ({ ...f, ...t }));
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIssues([]);
    setOkMessage(null);
    setErrorMsg(null);

    try {
      const res = await create.mutateAsync({
        facility_id: Number(form.facility_id),
        scope: Number(form.scope),
        category: form.category,
        subcategory: form.subcategory,
        activity_description: form.activity_description,
        quantity: Number(form.quantity),
        unit: form.unit,
        period_start: form.period_start,
        period_end: form.period_end,
        data_quality_score: Number(form.data_quality_score),
        uploaded_by: "manual",
      });
      setIssues(res.validation);
      setOkMessage(`Saved as activity #${res.activity.id}.`);
      setForm((f) => ({ ...f, quantity: "", activity_description: "" }));
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : String(err));
    }
  };

  const facilitiesList = facilities.data ?? [];

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <Field label="Facility">
          <select
            required
            className={selectCls}
            value={form.facility_id}
            onChange={(e) => update("facility_id", Number(e.target.value))}
          >
            <option value={0} disabled>
              Select facility…
            </option>
            {facilitiesList.map((f) => (
              <option key={f.id} value={f.id}>
                {f.name}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Scope">
          <select
            className={selectCls}
            value={form.scope}
            onChange={(e) => update("scope", Number(e.target.value))}
          >
            {SCOPE_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Category">
          <input
            required
            className={inputCls}
            value={form.category}
            onChange={(e) => update("category", e.target.value)}
          />
        </Field>

        <Field label="Subcategory">
          <input
            required
            className={inputCls}
            value={form.subcategory}
            onChange={(e) => update("subcategory", e.target.value)}
          />
        </Field>

        <Field label="Quantity">
          <input
            required
            type="number"
            step="any"
            min="0"
            className={inputCls}
            value={form.quantity}
            onChange={(e) => update("quantity", e.target.value)}
          />
        </Field>

        <Field label="Unit">
          <input
            required
            className={inputCls}
            value={form.unit}
            onChange={(e) => update("unit", e.target.value)}
          />
        </Field>

        <Field label="Period start">
          <input
            required
            type="date"
            className={inputCls}
            value={form.period_start}
            onChange={(e) => update("period_start", e.target.value)}
          />
        </Field>

        <Field label="Period end">
          <input
            required
            type="date"
            className={inputCls}
            value={form.period_end}
            onChange={(e) => update("period_end", e.target.value)}
          />
        </Field>

        <Field label="Activity description" className="md:col-span-2">
          <input
            required
            className={inputCls}
            value={form.activity_description}
            onChange={(e) => update("activity_description", e.target.value)}
          />
        </Field>

        <Field label="Data quality (1=spend / 5=metered)">
          <input
            type="number"
            min={1}
            max={5}
            className={inputCls}
            value={form.data_quality_score}
            onChange={(e) => update("data_quality_score", Number(e.target.value))}
          />
        </Field>
      </div>

      <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
        <span>Templates:</span>
        {(QUICK_TEMPLATES[form.scope] ?? []).map((t) => (
          <button
            key={`${t.category}-${t.subcategory}`}
            type="button"
            onClick={() => applyTemplate(t)}
            className="rounded-full border border-slate-200 px-2 py-0.5 hover:bg-slate-50"
          >
            {t.subcategory} ({t.unit})
          </button>
        ))}
      </div>

      <div className="flex items-center gap-3">
        <Button type="submit" disabled={create.isPending}>
          {create.isPending ? "Saving…" : "Save activity"}
        </Button>
        {okMessage && <span className="text-xs text-emerald-700">{okMessage}</span>}
        {errorMsg && <span className="text-xs text-danger">Save failed: {errorMsg}</span>}
      </div>

      {issues.length > 0 && (
        <div className="space-y-1">
          {issues.map((i, idx) => (
            <div
              key={idx}
              className={`rounded-md border px-3 py-2 text-xs ${
                i.severity === "error"
                  ? "border-danger/30 bg-red-50 text-danger"
                  : "border-amber-300/50 bg-amber-50 text-amber-800"
              }`}
            >
              <span className="font-medium uppercase">{i.severity}</span> · {i.field}: {i.message}
            </div>
          ))}
        </div>
      )}
    </form>
  );
}

const inputCls =
  "w-full rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand";
const selectCls = inputCls;

function Field({
  label,
  className,
  children,
}: {
  label: string;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <label className={`flex flex-col gap-1 ${className ?? ""}`}>
      <span className="text-xs font-medium text-slate-600">{label}</span>
      {children}
    </label>
  );
}
