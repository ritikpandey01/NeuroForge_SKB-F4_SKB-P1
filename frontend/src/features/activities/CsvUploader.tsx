import { useState } from "react";

import { Button } from "@/components/ui/button";

import { useCsvCommit, useCsvPreview } from "./api";
import { PreviewTable } from "./PreviewTable";
import type { ActivityCreate, CsvPreviewResponse } from "./types";

export function CsvUploader() {
  const preview = useCsvPreview();
  const commit = useCsvCommit();
  const [file, setFile] = useState<File | null>(null);
  const [previewData, setPreview] = useState<CsvPreviewResponse | null>(null);
  const [committed, setCommitted] = useState<{ inserted: number } | null>(null);

  const onPreview = async () => {
    if (!file) return;
    setCommitted(null);
    const result = await preview.mutateAsync({ file, uploadedBy: "csv" });
    setPreview(result);
  };

  const onCommit = async (rows: ActivityCreate[]) => {
    if (!rows.length) return;
    const result = await commit.mutateAsync(rows);
    setCommitted({ inserted: result.inserted });
    setPreview(null);
    setFile(null);
  };

  return (
    <div className="space-y-4">
      <div className="rounded-md border border-dashed border-slate-300 bg-slate-50 p-4">
        <div className="flex flex-wrap items-center gap-3">
          <input
            type="file"
            accept=".csv,text/csv"
            onChange={(e) => {
              setPreview(null);
              setCommitted(null);
              setFile(e.target.files?.[0] ?? null);
            }}
            className="text-sm"
          />
          <Button onClick={onPreview} disabled={!file || preview.isPending}>
            {preview.isPending ? "Parsing…" : "Preview"}
          </Button>
        </div>
        <p className="mt-2 text-xs text-slate-500">
          Required columns: facility_name, scope, category, subcategory,
          activity_description, quantity, unit, period_start, period_end. Dates
          accept YYYY-MM-DD or YYYY-MM. Max 5 MB.
        </p>
      </div>

      {preview.isError && (
        <div className="rounded-md border border-danger/30 bg-red-50 p-3 text-xs text-danger">
          Preview failed: {(preview.error as Error)?.message}
        </div>
      )}

      {committed && (
        <div className="rounded-md border border-emerald-300 bg-emerald-50 p-3 text-xs text-emerald-800">
          Committed {committed.inserted} rows. Dashboard will refresh.
        </div>
      )}

      {previewData && (
        <PreviewTable
          preview={previewData}
          onCommit={onCommit}
          committing={commit.isPending}
        />
      )}
    </div>
  );
}
