import { useState } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CsvUploader } from "@/features/activities/CsvUploader";
import { DocumentUploader } from "@/features/activities/DocumentUploader";
import { ManualEntryForm } from "@/features/activities/ManualEntryForm";
import { RecentActivities } from "@/features/activities/RecentActivities";

const TABS = [
  { id: "recent", label: "Recent activity" },
  { id: "manual", label: "Manual entry" },
  { id: "csv", label: "CSV upload" },
  { id: "document", label: "Document parse (AI)" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function DataManagement() {
  const [tab, setTab] = useState<TabId>("recent");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
          Data Management
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Capture activity data from manual entry, bulk CSV, or AI-parsed
          source documents. Outliers are flagged but never silently discarded;
          AI-extracted rows always require human confirmation.
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
          {tab === "recent" && <RecentActivities />}
          {tab === "manual" && <ManualEntryForm />}
          {tab === "csv" && <CsvUploader />}
          {tab === "document" && <DocumentUploader />}
        </CardContent>
      </Card>
    </div>
  );
}
