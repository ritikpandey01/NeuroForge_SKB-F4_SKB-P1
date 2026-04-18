"""Report generation endpoints (Module 10).

Deterministic PDF render first; LLM exec summary is opt-in via
`include_narrative=true` and degrades to 502 on upstream error rather than
blocking the PDF — the row is still saved with status=ready and the
narrative is simply omitted from the PDF.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, Response
from openai import APIError
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

import json

from app.api.deps import get_current_user, require_role
from app.api.scoping import ensure_report
from app.core.config import settings
from app.core.llm_client import CircuitBreakerOpen, LLMNotConfigured, llm
from app.db.models import Report, ReportAnchor, User, UserRole
from app.db.session import get_db
from app.schemas.anchor import (
    AnchorOut,
    ChainAnchorResponse,
    SealResponse,
    VerifyResponse,
)
from app.schemas.report import GenerateReportRequest, ReportNarrativeResponse, ReportOut
from app.services.anchoring import compute_report_root, verify_report_root
from app.services.assurance import build_bundle
from app.services.audit import write_audit
from app.services.chain_client import ChainError, submit_anchor
from app.services.report_renderer import build_context, render_pdf

router = APIRouter(prefix="/reports")


@router.get("", response_model=list[ReportOut])
def list_reports(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Report]:
    return list(
        db.scalars(
            select(Report)
            .where(Report.org_id == user.org_id)
            .order_by(desc(Report.generated_at))
            .limit(100)
        ).all()
    )


@router.post("/generate", response_model=ReportOut)
def generate(
    req: GenerateReportRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin, UserRole.analyst)),
) -> Report:
    # Insert row up front with status=generating so a crash leaves a diagnostic
    # trace in the DB — reports never disappear silently.
    report = Report(
        org_id=user.org_id,
        report_type=req.framework,
        period=req.period,
        status="generating",
    )
    db.add(report)
    db.flush()

    try:
        context = build_context(db, req.period, org_id=user.org_id)
    except ValueError as e:
        report.status = "failed"
        db.commit()
        raise HTTPException(422, str(e)) from e

    narrative_text: str | None = None
    if req.include_narrative:
        try:
            narrative_text = _generate_narrative(context, req.framework)
        except (LLMNotConfigured, CircuitBreakerOpen, APIError):
            narrative_text = None

    try:
        path = render_pdf(
            framework=req.framework,
            period=req.period,
            context=context,
            narrative=narrative_text,
            report_id=report.id,
        )
    except Exception as e:
        report.status = "failed"
        db.commit()
        raise HTTPException(500, f"PDF render failed: {e}") from e

    report.file_path = str(path)
    report.status = "ready"
    db.commit()
    db.refresh(report)
    return report


@router.get("/{report_id}/download")
def download(
    report_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> FileResponse:
    row = ensure_report(db, report_id, user.org_id)
    if row.status != "ready" or not row.file_path:
        raise HTTPException(409, f"report is {row.status}, no file to download")
    path = Path(row.file_path)
    if not path.exists():
        row.status = "failed"
        db.commit()
        raise HTTPException(410, "PDF file missing on disk — regenerate the report")
    filename = f"{row.report_type}_{row.period}.pdf"
    return FileResponse(str(path), media_type="application/pdf", filename=filename)


@router.post("/{report_id}/narrative", response_model=ReportNarrativeResponse)
def narrative(
    report_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin, UserRole.analyst)),
) -> ReportNarrativeResponse:
    """Generate (or regenerate) the AI exec summary for an existing report,
    independent of the initial render. Follows the same 503/502 pattern as
    scenarios/anomalies."""
    row = ensure_report(db, report_id, user.org_id)

    try:
        context = build_context(db, row.period, org_id=user.org_id)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e

    try:
        text = _generate_narrative(context, row.report_type)  # type: ignore[arg-type]
    except LLMNotConfigured as e:
        raise HTTPException(503, str(e)) from e
    except CircuitBreakerOpen as e:
        raise HTTPException(503, str(e)) from e
    except APIError as e:
        raise HTTPException(502, getattr(e, "message", None) or str(e)) from e

    return ReportNarrativeResponse(narrative=text, model=settings.OPENAI_MODEL)


# ── LLM narrative (shared by /generate and /{id}/narrative) ──────────


_SYSTEM_PROMPT = """You are drafting an executive summary for a corporate GHG disclosure.

You'll receive the total emissions, per-scope breakdown, top facilities, and top categories for the reporting period.

Write a 3-paragraph summary (≤220 words total):
1. Headline — total emissions, scope mix, 1-2 sentences on what the mix indicates (e.g. S3 dominance → value-chain is the material lever).
2. Where emissions concentrate — top 1-2 facilities and top 2-3 categories, framed as mitigation priorities.
3. One forward-looking commitment or methodology note the reader should take away (e.g. factor source, year coverage, what the company plans to do about the largest source).

Plain prose, no bullets, no headings. Use concrete numbers. Neutral auditor tone."""


def _build_user_prompt(context: dict, framework: str) -> str:
    scopes = ", ".join(
        f"S{row['scope']}: {row['tonnes']:,.0f} t ({row['pct']:.1f}%)"
        for row in context["by_scope"]
    )
    top_facilities = ", ".join(
        f"{f['name']} ({f['tonnes']:,.0f} t)" for f in context["by_facility"][:3]
    )
    top_cats = ", ".join(
        f"S{c['scope']} {c['category']} ({c['tonnes']:,.0f} t)"
        for c in context["by_category"][:5]
    )
    return (
        f"Framework: {framework}\n"
        f"Period: {context['period']} "
        f"({context['period_start']} – {context['period_end']})\n"
        f"Organization: {context['org'].name} ({context['org'].industry})\n"
        f"Total emissions: {context['total_tonnes']:,.1f} tCO2e\n"
        f"Scope mix: {scopes}\n"
        f"Top facilities: {top_facilities}\n"
        f"Top categories: {top_cats}\n"
        f"Suppliers engaged: {context['supplier_count']} "
        f"({context['submission_count']} quarterly submissions in period)\n"
        f"Activity records: {context['activity_row_count']}"
    )


# ── Seal / verify (Phase 1 — local Merkle anchor) ─────────────────────


@router.post("/{report_id}/seal", response_model=SealResponse)
def seal_report(
    report_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin)),
) -> SealResponse:
    """Compute the Merkle root over the report's inputs and store it.

    Phase 1: chain="local" (no blockchain tx). Phase 2 will upgrade this
    to submit the same root to Polygon."""
    report = ensure_report(db, report_id, user.org_id)

    existing = db.scalar(
        select(ReportAnchor)
        .where(ReportAnchor.report_id == report.id)
        .order_by(desc(ReportAnchor.sealed_at))
    )
    if existing is not None:
        raise HTTPException(
            409,
            f"report already sealed at {existing.sealed_at.isoformat()} "
            f"(root {existing.merkle_root}). Re-sealing is not permitted — "
            f"generate a fresh report instead.",
        )

    manifest = compute_report_root(db, report)
    anchor = ReportAnchor(
        report_id=report.id,
        org_id=user.org_id,
        merkle_root=manifest.report_root,
        manifest=json.dumps(manifest.to_dict(), sort_keys=True),
        chain="local",
        sealed_by=user.email,
    )
    db.add(anchor)
    db.flush()

    write_audit(
        db,
        user=user.email,
        org_id=user.org_id,
        action="seal",
        entity_type="report",
        entity_id=report.id,
        old_value=None,
        new_value=json.dumps({"merkle_root": manifest.report_root, "chain": "local"}),
    )
    db.commit()
    db.refresh(anchor)
    return SealResponse(
        anchor=AnchorOut.model_validate(anchor),
        manifest=manifest.to_dict(),
    )


@router.get("/{report_id}/verify", response_model=VerifyResponse)
def verify_report(
    report_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> VerifyResponse:
    """Recompute the Merkle root from live DB state and compare to the
    stored anchor. Any authenticated user can verify (transparency)."""
    report = ensure_report(db, report_id, user.org_id)
    anchor = db.scalar(
        select(ReportAnchor)
        .where(ReportAnchor.report_id == report.id)
        .order_by(desc(ReportAnchor.sealed_at))
    )
    if anchor is None:
        raise HTTPException(404, "report has not been sealed")

    stored_manifest = json.loads(anchor.manifest)
    result = verify_report_root(db, report, stored_manifest)
    return VerifyResponse(
        verified=result.verified,
        diverged_subtree=result.diverged_subtree,
        stored_root=result.stored_root,
        recomputed_root=result.recomputed_root,
        stored_manifest=result.stored,
        recomputed_manifest=result.recomputed,
        sealed_at=anchor.sealed_at,
        sealed_by=anchor.sealed_by,
        chain=anchor.chain,
        tx_hash=anchor.tx_hash,
        block_number=anchor.block_number,
    )


@router.post("/{report_id}/anchor", response_model=ChainAnchorResponse)
def anchor_onchain(
    report_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin)),
) -> ChainAnchorResponse:
    """Promote a locally-sealed report to an on-chain anchor.

    Requires a prior /seal (chain="local"). Submits the stored Merkle root to
    the configured chain (simulated or Polygon) and updates the anchor row
    with chain name, tx hash, and block number. 409 if already on-chain."""
    report = ensure_report(db, report_id, user.org_id)
    anchor = db.scalar(
        select(ReportAnchor)
        .where(ReportAnchor.report_id == report.id)
        .order_by(desc(ReportAnchor.sealed_at))
    )
    if anchor is None:
        raise HTTPException(404, "report has not been sealed — call /seal first")
    if anchor.chain != "local":
        raise HTTPException(
            409,
            f"report already anchored on {anchor.chain} "
            f"(tx {anchor.tx_hash}) at block {anchor.block_number}",
        )

    try:
        receipt = submit_anchor(user.org_id, report.period, anchor.merkle_root)
    except ChainError as e:
        # 503 when the chain isn't reachable / not configured, 502 for other upstream.
        msg = str(e)
        status = 503 if "requires" in msg or "cannot reach" in msg else 502
        raise HTTPException(status, f"chain anchor failed: {msg}") from e

    anchor.chain = receipt.chain
    anchor.tx_hash = receipt.tx_hash
    anchor.block_number = receipt.block_number
    db.flush()

    write_audit(
        db,
        user=user.email,
        org_id=user.org_id,
        action="anchor",
        entity_type="report",
        entity_id=report.id,
        old_value=json.dumps({"chain": "local"}),
        new_value=json.dumps(
            {
                "chain": receipt.chain,
                "tx_hash": receipt.tx_hash,
                "block_number": receipt.block_number,
            }
        ),
    )
    db.commit()
    db.refresh(anchor)
    return ChainAnchorResponse(
        anchor=AnchorOut.model_validate(anchor),
        explorer_url=receipt.explorer_url,
    )


@router.get("/{report_id}/anchor", response_model=AnchorOut)
def get_anchor(
    report_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ReportAnchor:
    report = ensure_report(db, report_id, user.org_id)
    anchor = db.scalar(
        select(ReportAnchor)
        .where(ReportAnchor.report_id == report.id)
        .order_by(desc(ReportAnchor.sealed_at))
    )
    if anchor is None:
        raise HTTPException(404, "report has not been sealed")
    return anchor


@router.get("/{report_id}/assurance.zip")
def assurance_bundle(
    report_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    """Self-contained proof bundle for a sealed report.

    Any authenticated user in the org can download — transparency is the
    point. Contains manifest, leaves, methodology, PDF, certificate, and
    a stdlib-only verify.py."""
    report = ensure_report(db, report_id, user.org_id)
    anchor = db.scalar(
        select(ReportAnchor)
        .where(ReportAnchor.report_id == report.id)
        .order_by(desc(ReportAnchor.sealed_at))
    )
    if anchor is None:
        raise HTTPException(404, "report has not been sealed — nothing to export")
    payload = build_bundle(db, report, anchor)
    filename = f"assurance_{report.report_type}_{report.period}_{report.id}.zip"
    return Response(
        content=payload,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _generate_narrative(context: dict, framework: str) -> str:
    resp = llm.chat_completions_create(
        model=settings.OPENAI_MODEL,
        max_tokens=450,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(context, framework)},
        ],
    )
    text = (resp.choices[0].message.content or "").strip()
    if not text:
        raise APIError("LLM returned empty narrative.", body=None, request=None)
    return text
