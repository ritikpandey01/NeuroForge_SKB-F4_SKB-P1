import { FileText, Sparkles } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api";

import { useGenerateReport } from "./api";
import { FRAMEWORKS } from "./types";
import type { Framework } from "./types";

export function GenerateReport() {
  const [framework, setFramework] = useState<Framework>("BRSR");
  const [period, setPeriod] = useState<string>("FY2024");
  const [includeNarrative, setIncludeNarrative] = useState<boolean>(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const mutation = useGenerateReport();

  const onGenerate = async () => {
    setMsg(null);
    setError(null);
    try {
      const r = await mutation.mutateAsync({
        framework,
        period: period.trim(),
        include_narrative: includeNarrative,
      });
      setMsg(`${r.report_type} ${r.period} generated — download from the list below.`);
    } catch (e) {
      if (e instanceof ApiError) {
        setError(e.message);
      } else {
        setError(e instanceof Error ? e.message : String(e));
      }
    }
  };

  const blurb = FRAMEWORKS.find((f) => f.value === framework)?.blurb;

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-3">
        <div>
          <label className="text-[11px] font-semibold uppercase tracking-widest text-slate-500">
            Framework
          </label>
          <div className="mt-1 flex gap-1 rounded-md border border-slate-200 p-0.5">
            {FRAMEWORKS.map((f) => (
              <button
                key={f.value}
                type="button"
                onClick={() => setFramework(f.value)}
                className={`flex-1 rounded px-2 py-1 text-xs font-medium transition-colors ${
                  framework === f.value
                    ? "bg-brand text-white"
                    : "text-slate-600 hover:bg-slate-50"
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="text-[11px] font-semibold uppercase tracking-widest text-slate-500">
            Reporting period
          </label>
          <input
            type="text"
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            placeholder="FY2024 or 2024"
            className="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
          />
          <p className="mt-1 text-[10px] text-slate-400">
            Use <code>FYYYYY</code> (Apr–Mar) or <code>YYYY</code> (Jan–Dec).
          </p>
        </div>

        <div>
          <label className="text-[11px] font-semibold uppercase tracking-widest text-slate-500">
            AI exec summary
          </label>
          <label className="mt-1 flex cursor-pointer items-center gap-2 rounded-md border border-slate-200 px-3 py-1.5 text-xs">
            <input
              type="checkbox"
              checked={includeNarrative}
              onChange={(e) => setIncludeNarrative(e.target.checked)}
              className="accent-teal-600"
            />
            <Sparkles size={12} className="text-brand" />
            <span className="text-slate-700">Include AI narrative in PDF</span>
          </label>
          <p className="mt-1 text-[10px] text-slate-400">
            Soft-fails if OPENAI_API_KEY is unset — PDF still generates.
          </p>
        </div>
      </div>

      {blurb && (
        <p className="rounded-md border border-slate-100 bg-slate-50/60 px-3 py-2 text-xs text-slate-500">
          {blurb}
        </p>
      )}

      <div className="flex items-center gap-3">
        <Button onClick={onGenerate} disabled={mutation.isPending || !period.trim()}>
          <FileText size={14} />
          {mutation.isPending ? "Generating PDF…" : "Generate report"}
        </Button>
        {msg && <span className="text-xs text-success">{msg}</span>}
        {error && <span className="text-xs text-danger">{error}</span>}
      </div>
    </div>
  );
}
