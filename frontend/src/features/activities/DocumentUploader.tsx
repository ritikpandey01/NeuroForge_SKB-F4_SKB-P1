import { useState } from "react";

import { Button } from "@/components/ui/button";

import { useCsvCommit, useDocumentPreview, useDocumentTypes } from "./api";
import { PreviewTable } from "./PreviewTable";
import type { ActivityCreate, CsvPreviewResponse } from "./types";

const ACCEPT = ".pdf,.png,.jpg,.jpeg,.webp,application/pdf,image/png,image/jpeg,image/webp";

const DOC_TYPE_LABELS: Record<string, string> = {
  electricity_bill: "Electricity bill (Scope 2 · grid)",
  fuel_invoice: "Fuel invoice — diesel / petrol / LPG (Scope 1)",
  natural_gas_bill: "Natural gas / PNG bill (Scope 1)",
  material_purchase: "Material purchase — steel / aluminium / etc. (Scope 3)",
  freight_invoice: "Freight / logistics invoice (Scope 3)",
  travel_itinerary: "Business travel itinerary (Scope 3)",
  waste_disposal: "Waste disposal receipt (Scope 3)",
  supplier_disclosure: "Supplier emissions disclosure (not an invoice)",
};

export function DocumentUploader() {
  const preview = useDocumentPreview();
  const commit = useCsvCommit();
  const types = useDocumentTypes();
  const [file, setFile] = useState<File | null>(null);
  const [docType, setDocType] = useState<string>("auto");
  const [previewData, setPreview] = useState<CsvPreviewResponse | null>(null);
  const [committed, setCommitted] = useState<{ inserted: number } | null>(null);

  const onPreview = async () => {
    if (!file) return;
    setCommitted(null);
    const result = await preview.mutateAsync({
      file,
      uploadedBy: "document",
      docType,
    });
    setPreview(result);
  };

  const onCommit = async (rows: ActivityCreate[]) => {
    if (!rows.length) return;
    const result = await commit.mutateAsync(rows);
    setCommitted({ inserted: result.inserted });
    setPreview(null);
    setFile(null);
  };

  const onDrop = (e: React.DragEvent<HTMLLabelElement>) => {
    e.preventDefault();
    const dropped = e.dataTransfer.files?.[0];
    if (dropped) {
      setPreview(null);
      setCommitted(null);
      setFile(dropped);
    }
  };

  const availableTypes = types.data?.types ?? [];

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-1">
        <label
          htmlFor="doc-type"
          className="text-[11px] font-semibold uppercase tracking-widest text-slate-500"
        >
          Document type
        </label>
        <select
          id="doc-type"
          value={docType}
          onChange={(e) => setDocType(e.target.value)}
          disabled={preview.isPending}
          className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand disabled:bg-slate-50"
        >
          <option value="auto">Auto-detect (let the AI decide)</option>
          {availableTypes.map((t) => (
            <option key={t.key} value={t.key}>
              {DOC_TYPE_LABELS[t.key] ?? t.key}
            </option>
          ))}
        </select>
        <div className="text-[11px] text-slate-500">
          {docType === "auto"
            ? "No hint — the model classifies the document itself. Best when unsure."
            : "Hint sent to the model — improves accuracy when the document is messy or low-quality."}
        </div>
      </div>

      <label
        htmlFor="doc-input"
        onDragOver={(e) => e.preventDefault()}
        onDrop={onDrop}
        className="flex cursor-pointer flex-col items-center justify-center rounded-md border-2 border-dashed border-slate-300 bg-slate-50 p-6 text-center transition-colors hover:border-brand/40 hover:bg-brand/5"
      >
        <input
          id="doc-input"
          type="file"
          accept={ACCEPT}
          onChange={(e) => {
            setPreview(null);
            setCommitted(null);
            setFile(e.target.files?.[0] ?? null);
          }}
          className="hidden"
        />
        <div className="text-sm font-medium text-slate-700">
          {file ? file.name : "Drop a utility bill or invoice here, or click to browse"}
        </div>
        <div className="mt-1 text-xs text-slate-500">
          PDF, PNG, JPG, or WebP · max 10 MB · parsed by Claude
        </div>
        {file && (
          <div className="mt-1 text-[11px] text-slate-400">
            {(file.size / 1024).toFixed(1)} KB · {file.type || "unknown type"}
          </div>
        )}
      </label>

      <div className="flex items-center gap-3">
        <Button onClick={onPreview} disabled={!file || preview.isPending}>
          {preview.isPending ? "Asking Claude…" : "Extract activities"}
        </Button>
        <span className="text-xs text-slate-500">
          The model returns rows for you to review before they hit the ledger.
        </span>
      </div>

      {preview.isError && (
        <div className="rounded-md border border-danger/30 bg-red-50 p-3 text-xs text-danger">
          Extraction failed: {(preview.error as Error)?.message}
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
