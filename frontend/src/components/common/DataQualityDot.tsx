import { cn } from "@/lib/utils";

type Level = "verified" | "estimated" | "flagged";

const styles: Record<Level, string> = {
  verified: "bg-success",
  estimated: "bg-warn",
  flagged: "bg-danger",
};

const labels: Record<Level, string> = {
  verified: "Verified",
  estimated: "Estimated",
  flagged: "Flagged",
};

export function DataQualityDot({ level, withLabel = false }: { level: Level; withLabel?: boolean }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={cn("inline-block h-2 w-2 rounded-full", styles[level])} aria-label={labels[level]} />
      {withLabel && <span className="text-xs text-slate-600">{labels[level]}</span>}
    </span>
  );
}
