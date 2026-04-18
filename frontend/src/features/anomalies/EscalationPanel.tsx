import { CheckCircle2, Gavel, ShieldAlert } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";

import { useBoardReviewAnomaly, useEscalateAnomaly } from "./api";
import type { Anomaly } from "./types";

type Props = {
  anomaly: Anomaly;
};

export function EscalationPanel({ anomaly }: Props) {
  const escalate = useEscalateAnomaly();
  const review = useBoardReviewAnomaly();
  const [showForm, setShowForm] = useState(false);
  const [owner, setOwner] = useState("esg.lead@greenfieldmfg.in");
  const [dueDate, setDueDate] = useState("");
  const [notes, setNotes] = useState("");
  const [reviewer, setReviewer] = useState("chair@greenfieldmfg.in");
  const [reviewNotes, setReviewNotes] = useState("");

  const canEscalate =
    anomaly.escalation_status === null &&
    (anomaly.severity === "critical" || anomaly.severity === "high");

  const onEscalate = async () => {
    await escalate.mutateAsync({
      id: anomaly.id,
      body: {
        owner,
        due_date: dueDate || null,
        notes: notes || null,
      },
    });
    setShowForm(false);
  };

  const onReview = async () => {
    await review.mutateAsync({
      id: anomaly.id,
      body: { reviewer, notes: reviewNotes || null },
    });
  };

  if (anomaly.escalation_status === "board_reviewed") {
    return (
      <div className="mt-3 flex items-start gap-2 rounded-md bg-emerald-50 p-3 text-xs text-emerald-900 ring-1 ring-inset ring-emerald-200">
        <CheckCircle2 size={14} className="mt-0.5 text-emerald-700" />
        <div>
          <div className="font-semibold uppercase tracking-wide">
            Reviewed by board
          </div>
          {anomaly.board_reviewed_at && (
            <div className="text-emerald-800">
              {new Date(anomaly.board_reviewed_at).toLocaleString()}
            </div>
          )}
          {anomaly.escalation_notes && (
            <div className="mt-1 whitespace-pre-wrap text-emerald-900/80">
              {anomaly.escalation_notes}
            </div>
          )}
        </div>
      </div>
    );
  }

  if (anomaly.escalation_status === "escalated") {
    return (
      <div className="mt-3 space-y-2 rounded-md bg-violet-50 p-3 text-xs text-violet-900 ring-1 ring-inset ring-violet-200">
        <div className="flex items-start gap-2">
          <ShieldAlert size={14} className="mt-0.5 text-violet-700" />
          <div className="flex-1">
            <div className="font-semibold uppercase tracking-wide">
              Escalated to board
            </div>
            <div className="text-violet-800">
              Owner:{" "}
              <span className="font-mono">{anomaly.escalation_owner}</span>
              {anomaly.escalation_due_date ? (
                <>
                  {" · Due "}
                  {anomaly.escalation_due_date}
                </>
              ) : null}
            </div>
            {anomaly.escalation_notes && (
              <div className="mt-1 text-violet-900/80">
                {anomaly.escalation_notes}
              </div>
            )}
          </div>
        </div>
        <div className="flex flex-col gap-2 border-t border-violet-200 pt-2">
          <div className="flex flex-col gap-2 sm:flex-row">
            <input
              type="text"
              value={reviewer}
              onChange={(e) => setReviewer(e.target.value)}
              placeholder="Reviewer email"
              className="h-7 flex-1 rounded-md border border-violet-200 bg-white px-2 text-xs"
            />
            <input
              type="text"
              value={reviewNotes}
              onChange={(e) => setReviewNotes(e.target.value)}
              placeholder="Decision notes (optional)"
              className="h-7 flex-[2] rounded-md border border-violet-200 bg-white px-2 text-xs"
            />
          </div>
          <div className="flex justify-end">
            <Button
              variant="default"
              size="sm"
              onClick={onReview}
              disabled={review.isPending || !reviewer}
            >
              <Gavel size={12} />
              {review.isPending ? "Recording…" : "Mark as reviewed"}
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (!canEscalate) return null;

  if (!showForm) {
    return (
      <div className="mt-3">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowForm(true)}
          title="Flag this item for board oversight"
        >
          <ShieldAlert size={12} />
          Escalate to board
        </Button>
      </div>
    );
  }

  return (
    <div className="mt-3 space-y-2 rounded-md bg-white p-3 text-xs ring-1 ring-inset ring-slate-200">
      <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
        Escalate to board
      </div>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        <label className="flex flex-col gap-1">
          <span className="text-slate-500">Owner</span>
          <input
            type="text"
            value={owner}
            onChange={(e) => setOwner(e.target.value)}
            className="h-7 rounded-md border border-slate-300 bg-white px-2 text-xs"
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-slate-500">Due date</span>
          <input
            type="date"
            value={dueDate}
            onChange={(e) => setDueDate(e.target.value)}
            className="h-7 rounded-md border border-slate-300 bg-white px-2 text-xs"
          />
        </label>
      </div>
      <label className="flex flex-col gap-1">
        <span className="text-slate-500">Notes for the board</span>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={2}
          className="rounded-md border border-slate-300 bg-white p-2 text-xs"
          placeholder="Why this needs board attention…"
        />
      </label>
      <div className="flex justify-end gap-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setShowForm(false)}
          disabled={escalate.isPending}
        >
          Cancel
        </Button>
        <Button
          variant="default"
          size="sm"
          onClick={onEscalate}
          disabled={escalate.isPending || !owner}
        >
          {escalate.isPending ? "Escalating…" : "Escalate"}
        </Button>
      </div>
    </div>
  );
}
