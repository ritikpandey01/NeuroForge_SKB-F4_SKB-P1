import { Download, Lock, Sparkles } from "lucide-react";
import { Fragment, useState } from "react";

import { ErrorState, LoadingState } from "@/components/common/LoadingState";
import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api";

import { downloadUrl, useReportNarrative, useReports } from "./api";
import { ReportSealPanel } from "./ReportSealPanel";
import type { ReportStatus } from "./types";

const STATUS_STYLES: Record<ReportStatus, string> = {
  pending: "bg-slate-100 text-slate-600",
  generating: "bg-amber-100 text-amber-800",
  ready: "bg-emerald-50 text-emerald-700",
  failed: "bg-red-50 text-red-700",
};

export function ReportList() {
  const list = useReports();
  const narrative = useReportNarrative();
  const [openId, setOpenId] = useState<number | null>(null);
  const [narrText, setNarrText] = useState<string | null>(null);
  const [narrError, setNarrError] = useState<string | null>(null);
  const [sealOpenId, setSealOpenId] = useState<number | null>(null);

  const onShowNarrative = async (id: number) => {
    setOpenId(id);
    setNarrText(null);
    setNarrError(null);
    try {
      const res = await narrative.mutateAsync(id);
      setNarrText(res.narrative);
    } catch (e) {
      if (e instanceof ApiError && e.status === 503) {
        setNarrError(`AI narrative unavailable: ${e.message}`);
      } else if (e instanceof ApiError) {
        setNarrError(e.message);
      } else {
        setNarrError(e instanceof Error ? e.message : String(e));
      }
    }
  };

  if (list.isLoading) return <LoadingState label="Loading reports…" />;
  if (list.isError) return <ErrorState error={list.error} />;
  if (!list.data || list.data.length === 0) {
    return (
      <div className="rounded-md border border-dashed border-slate-200 p-8 text-center text-sm text-slate-400">
        No reports yet. Generate one above.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-md border border-slate-200">
      <table className="w-full text-sm">
        <thead className="bg-slate-50 text-[10px] uppercase tracking-widest text-slate-500">
          <tr>
            <th className="px-3 py-2 text-left">Framework</th>
            <th className="px-3 py-2 text-left">Period</th>
            <th className="px-3 py-2 text-left">Generated</th>
            <th className="px-3 py-2 text-left">Status</th>
            <th className="px-3 py-2 text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {list.data.map((r) => (
            <Fragment key={r.id}>
              <tr className="border-t border-slate-100 hover:bg-slate-50/40">
                <td className="px-3 py-2 font-medium text-slate-800">{r.report_type}</td>
                <td className="px-3 py-2 font-mono text-xs text-slate-600">{r.period}</td>
                <td className="px-3 py-2 text-xs text-slate-500">
                  {new Date(r.generated_at).toLocaleString()}
                </td>
                <td className="px-3 py-2">
                  <span
                    className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${STATUS_STYLES[r.status]}`}
                  >
                    {r.status}
                  </span>
                </td>
                <td className="px-3 py-2">
                  <div className="flex items-center justify-end gap-1">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        setSealOpenId(sealOpenId === r.id ? null : r.id)
                      }
                      title="Cryptographic seal & verification"
                    >
                      <Lock size={12} />
                      Seal
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onShowNarrative(r.id)}
                      disabled={narrative.isPending && openId === r.id}
                      title="Generate an AI exec summary for this report"
                    >
                      <Sparkles size={12} />
                      {narrative.isPending && openId === r.id ? "…" : "AI summary"}
                    </Button>
                    <a
                      href={downloadUrl(r.id)}
                      target="_blank"
                      rel="noreferrer"
                      className={`inline-flex h-8 items-center gap-1 rounded-md px-3 text-xs font-medium transition-colors ${
                        r.status === "ready"
                          ? "bg-brand text-white hover:bg-brand-800"
                          : "pointer-events-none border border-slate-200 bg-slate-50 text-slate-400"
                      }`}
                    >
                      <Download size={12} />
                      PDF
                    </a>
                  </div>
                </td>
              </tr>
              {sealOpenId === r.id && (
                <tr className="bg-slate-50/40">
                  <td colSpan={5} className="px-4 py-3">
                    <ReportSealPanel reportId={r.id} reportStatus={r.status} />
                  </td>
                </tr>
              )}
              {openId === r.id && (narrText || narrError) && (
                <tr className="bg-slate-50/60">
                  <td colSpan={5} className="px-4 py-3">
                    {narrError ? (
                      <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900">
                        {narrError}
                      </div>
                    ) : (
                      <div className="space-y-2 text-xs leading-relaxed text-slate-700">
                        <div className="flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                          <Sparkles size={10} />
                          AI exec summary
                        </div>
                        {narrText!.split("\n").map((p, i) => (
                          <p key={i}>{p}</p>
                        ))}
                      </div>
                    )}
                  </td>
                </tr>
              )}
            </Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}
