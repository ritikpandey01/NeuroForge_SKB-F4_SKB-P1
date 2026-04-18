import { Sparkles } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api";

import { useNarrative } from "./api";
import type { ScenarioResponse } from "./types";

type Props = { scenario: ScenarioResponse | null };

export function NarrativePanel({ scenario }: Props) {
  const narrative = useNarrative();
  const [text, setText] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [stale, setStale] = useState(false);

  const onGenerate = async () => {
    if (!scenario) return;
    setError(null);
    setStale(false);
    try {
      const res = await narrative.mutateAsync(scenario);
      setText(res.narrative);
    } catch (e) {
      setText(null);
      if (e instanceof ApiError) {
        if (e.status === 503) {
          setError(
            `AI narrative unavailable: ${e.message}. The scenario math above is still valid.`,
          );
        } else if (e.status === 502) {
          setError(`LLM upstream error: ${e.message}`);
        } else {
          setError(e.message);
        }
      } else {
        setError(e instanceof Error ? e.message : String(e));
      }
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-widest text-slate-500">
            <Sparkles size={12} />
            AI transition analysis
          </div>
          <p className="mt-1 text-xs text-slate-500">
            Plain-English narrative grounded in the scenario numbers. Optional —
            the math above stands on its own.
          </p>
        </div>
        <Button
          size="sm"
          onClick={onGenerate}
          disabled={!scenario || narrative.isPending}
          onMouseEnter={() => {
            if (text) setStale(true);
          }}
        >
          {narrative.isPending ? "Generating…" : text ? "Regenerate" : "Generate narrative"}
        </Button>
      </div>

      {error && (
        <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900">
          {error}
        </div>
      )}

      {text && (
        <div className="relative rounded-md border border-slate-200 bg-white p-4 text-sm leading-relaxed text-slate-700 ring-1 ring-inset ring-slate-100">
          {stale && (
            <div className="absolute right-3 top-2 text-[10px] uppercase tracking-wider text-amber-600">
              May be stale — regenerate
            </div>
          )}
          {text.split("\n").map((para, i) => (
            <p key={i} className="mb-2 last:mb-0">
              {para}
            </p>
          ))}
        </div>
      )}

      {!text && !error && (
        <div className="rounded-md border border-dashed border-slate-200 p-6 text-center text-xs text-slate-400">
          Click "Generate narrative" for an AI-written transition-plan summary of the current scenario.
        </div>
      )}
    </div>
  );
}
