import {
  AlertTriangle,
  CheckCircle2,
  ExternalLink,
  FileArchive,
  Link as LinkIcon,
  Lock,
  ShieldCheck,
} from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";
import { ApiError } from "@/lib/api";

import {
  downloadAssuranceBundle,
  useAnchorOnChain,
  useReportAnchor,
  useSealReport,
  useVerifyReport,
} from "./api";
import type { VerifyResponse } from "./types";

interface Props {
  reportId: number;
  reportStatus: string;
}

function shortHash(h: string | null | undefined): string {
  if (!h) return "—";
  return h.length > 18 ? `${h.slice(0, 10)}…${h.slice(-6)}` : h;
}

function ManifestRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 py-0.5">
      <span className="text-[10px] uppercase tracking-wider text-slate-500">{label}</span>
      <span className="font-mono text-[11px] text-slate-700">{value}</span>
    </div>
  );
}

export function ReportSealPanel({ reportId, reportStatus }: Props) {
  const { hasRole } = useAuth();
  const anchor = useReportAnchor(reportId);
  const seal = useSealReport();
  const verify = useVerifyReport();
  const anchorChain = useAnchorOnChain();
  const [verifyResult, setVerifyResult] = useState<VerifyResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [explorerUrl, setExplorerUrl] = useState<string | null>(null);
  const [bundleLoading, setBundleLoading] = useState(false);

  const canSeal = hasRole("admin") && reportStatus === "ready" && !anchor.data;
  const canAnchor =
    hasRole("admin") && anchor.data !== null && anchor.data?.chain === "local";

  const onSeal = async () => {
    setError(null);
    try {
      await seal.mutateAsync(reportId);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
    }
  };

  const onVerify = async () => {
    setError(null);
    setVerifyResult(null);
    try {
      const res = await verify.mutateAsync(reportId);
      setVerifyResult(res);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
    }
  };

  const onDownloadBundle = async () => {
    setError(null);
    setBundleLoading(true);
    try {
      await downloadAssuranceBundle(reportId);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
    } finally {
      setBundleLoading(false);
    }
  };

  const onAnchorChain = async () => {
    setError(null);
    setExplorerUrl(null);
    try {
      const res = await anchorChain.mutateAsync(reportId);
      setExplorerUrl(res.explorer_url);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
    }
  };

  if (anchor.isLoading) {
    return <div className="text-xs text-slate-500">Loading anchor…</div>;
  }

  return (
    <div className="space-y-3 rounded-md border border-slate-200 bg-slate-50/60 p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-600">
          <Lock size={12} />
          Cryptographic seal
        </div>
        <div className="flex items-center gap-1">
          {!anchor.data && canSeal && (
            <Button
              variant="outline"
              size="sm"
              onClick={onSeal}
              disabled={seal.isPending}
              title="Compute Merkle root over activity rows, factors, evidence, methodology, and PDF. Stores the root so any later tamper is detectable."
            >
              <Lock size={12} />
              {seal.isPending ? "Sealing…" : "Seal report"}
            </Button>
          )}
          {canAnchor && (
            <Button
              variant="outline"
              size="sm"
              onClick={onAnchorChain}
              disabled={anchorChain.isPending}
              title="Submit the Merkle root to Polygon (or simulated chain in demo mode). Records tx hash + block number."
            >
              <LinkIcon size={12} />
              {anchorChain.isPending ? "Anchoring…" : "Anchor on-chain"}
            </Button>
          )}
          {anchor.data && (
            <Button
              variant="outline"
              size="sm"
              onClick={onVerify}
              disabled={verify.isPending}
            >
              <ShieldCheck size={12} />
              {verify.isPending ? "Verifying…" : "Verify now"}
            </Button>
          )}
          {anchor.data && (
            <Button
              variant="outline"
              size="sm"
              onClick={onDownloadBundle}
              disabled={bundleLoading}
              title="Download a self-contained zip an auditor can run verify.py against."
            >
              <FileArchive size={12} />
              {bundleLoading ? "Preparing…" : "Assurance bundle"}
            </Button>
          )}
        </div>
      </div>

      {!anchor.data ? (
        <div className="text-xs text-slate-500">
          {canSeal
            ? "Not sealed yet. Sealing creates a tamper-evident Merkle root over every input to this report — activity rows, factor versions, evidence files, methodology, and the PDF itself."
            : reportStatus !== "ready"
              ? "Report must be in 'ready' state before it can be sealed."
              : "Only admins can seal reports. Ask an admin on your team."}
        </div>
      ) : (
        <div className="space-y-2 text-xs">
          <div className="flex items-center gap-2 rounded-md bg-emerald-50 px-3 py-2 text-emerald-800">
            <CheckCircle2 size={14} />
            <div>
              <div className="font-semibold">Sealed</div>
              <div className="text-[11px] text-emerald-700">
                by {anchor.data.sealed_by} · {new Date(anchor.data.sealed_at).toLocaleString()} ·{" "}
                chain: {anchor.data.chain}
                {anchor.data.block_number
                  ? ` · block ${anchor.data.block_number}`
                  : ""}
              </div>
            </div>
          </div>
          <div className="rounded-md border border-slate-200 bg-white p-3">
            <ManifestRow label="Merkle root" value={shortHash(anchor.data.merkle_root)} />
            {anchor.data.tx_hash && (
              <ManifestRow label="Tx hash" value={shortHash(anchor.data.tx_hash)} />
            )}
            {explorerUrl && (
              <div className="mt-2 flex justify-end">
                <a
                  href={explorerUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 text-[11px] text-brand hover:underline"
                >
                  <ExternalLink size={10} />
                  View on PolygonScan
                </a>
              </div>
            )}
          </div>
          {anchor.data.chain === "local" && (
            <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-[11px] text-amber-800">
              Sealed locally. Click <span className="font-semibold">Anchor on-chain</span> to
              submit the root to Polygon for public verifiability.
            </div>
          )}
        </div>
      )}

      {verifyResult && (
        <div
          className={`rounded-md px-3 py-2 text-xs ${
            verifyResult.verified
              ? "bg-emerald-50 text-emerald-800"
              : "bg-red-50 text-red-800"
          }`}
        >
          <div className="mb-1 flex items-center gap-2 font-semibold">
            {verifyResult.verified ? (
              <>
                <CheckCircle2 size={14} />
                Verified — no tampering detected
              </>
            ) : (
              <>
                <AlertTriangle size={14} />
                Tamper detected — {verifyResult.diverged_subtree} diverged
              </>
            )}
          </div>
          <div className="mt-2 rounded bg-white/60 p-2 font-mono text-[10px] leading-relaxed">
            <div>stored:     {shortHash(verifyResult.stored_root)}</div>
            <div>recomputed: {shortHash(verifyResult.recomputed_root)}</div>
          </div>
          {!verifyResult.verified && (
            <div className="mt-2 text-[11px]">
              The {verifyResult.diverged_subtree?.replace("_root", "")} data has been altered
              since this report was sealed. Compare the stored and recomputed manifests below
              to identify what changed.
            </div>
          )}
        </div>
      )}

      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-800">
          {error}
        </div>
      )}
    </div>
  );
}
