import { useState } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ImpactMatrix } from "@/features/suppliers/ImpactMatrix";
import { SubmissionForm } from "@/features/suppliers/SubmissionForm";
import { SupplierRegistry } from "@/features/suppliers/SupplierRegistry";

const TABS = [
  { id: "registry", label: "Registry" },
  { id: "matrix", label: "Impact matrix" },
  { id: "submit", label: "Submit data" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function Suppliers() {
  const [tab, setTab] = useState<TabId>("registry");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
          Supplier Engagement
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Registry of tier-1/2/3 suppliers, portfolio-level data-maturity matrix,
          and the quarterly submission workflow that drives Scope 3 roll-ups.
        </p>
      </div>

      <div className="flex gap-1 border-b border-slate-200">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`-mb-px border-b-2 px-3 py-2 text-sm font-medium transition-colors ${
              tab === t.id
                ? "border-brand text-brand"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{TABS.find((t) => t.id === tab)?.label}</CardTitle>
        </CardHeader>
        <CardContent>
          {tab === "registry" && <SupplierRegistry />}
          {tab === "matrix" && <ImpactMatrix />}
          {tab === "submit" && <SubmissionForm />}
        </CardContent>
      </Card>
    </div>
  );
}
