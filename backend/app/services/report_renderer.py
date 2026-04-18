"""Report renderer — framework-specific PDF assembly (Module 10).

Uses ReportLab Platypus rather than HTML → WeasyPrint. ReportLab is already a
dependency, has no system-level requirements (no Cairo/Pango), and Platypus
flowables map cleanly onto the section-heavy structure of BRSR/GRI/TCFD
disclosures — each framework is a list of (title, paragraph, table) flowables
composed over a shared base layout.

Framework differences are narrow — they mostly rename sections, re-order
tables, and add a framework-specific "disclosure index" mapping each number
in the report back to its source. The KPI numbers themselves are identical
across frameworks (they resolve through the same emissions traceability
chain), so the renderer pulls context once and each framework formats it.

Outputs land in `settings.pdf_output_path` with filename
`{framework}_{period}_{report_id}.pdf`. The `Report` row stores the absolute
path so `/reports/{id}/download` can stream it back.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Literal

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import (
    ActivityData,
    Emission,
    EmissionFactor,
    Facility,
    Organization,
    Supplier,
    SupplierSubmission,
)

Framework = Literal["BRSR", "GRI", "TCFD"]

KG_PER_TONNE = 1000.0
BRAND_COLOR = colors.HexColor("#0F766E")
SLATE_900 = colors.HexColor("#0F172A")
SLATE_500 = colors.HexColor("#64748B")
SLATE_200 = colors.HexColor("#E2E8F0")


# ── Period parsing ────────────────────────────────────────────────────


def parse_period(period: str) -> tuple[date, date]:
    """Accepts 'FY2024' → (2024-04-01, 2025-03-31) [Indian FY] OR
    'FY2024-25' → same OR a 'YYYY' calendar year → Jan-Dec.

    We use the Indian FY convention for BRSR (Apr–Mar). Calendar years are
    allowed for flexibility with GRI/TCFD tenants that prefer Jan–Dec."""
    p = period.strip().upper().replace(" ", "")
    if p.startswith("FY"):
        year = int(p[2:6])
        return date(year, 4, 1), date(year + 1, 3, 31)
    if p.isdigit() and len(p) == 4:
        year = int(p)
        return date(year, 1, 1), date(year, 12, 31)
    raise ValueError(
        f"Could not parse period '{period}'. Use 'FY2024' (Apr–Mar) or '2024' (Jan–Dec)."
    )


# ── Context builder ───────────────────────────────────────────────────


def build_context(db: Session, period: str, *, org_id: int) -> dict[str, Any]:
    """Pull everything a report needs in one pass. DB-read-only."""
    start, end = parse_period(period)

    org = db.get(Organization, org_id)
    if not org:
        raise ValueError(f"organization {org_id} not found")

    # Emissions joined with activity + facility + factor, filtered to period.
    rows = db.execute(
        select(Emission, ActivityData, Facility, EmissionFactor)
        .join(ActivityData, Emission.activity_data_id == ActivityData.id)
        .join(Facility, ActivityData.facility_id == Facility.id)
        .outerjoin(EmissionFactor, Emission.emission_factor_id == EmissionFactor.id)
        .where(Facility.org_id == org_id)
        .where(ActivityData.period_start >= start, ActivityData.period_end <= end)
    ).all()

    if not rows:
        raise ValueError(
            f"No emissions in period {period} ({start} → {end}). "
            f"Add activity data or pick a different period."
        )

    total_kg = 0.0
    by_scope: dict[int, float] = defaultdict(float)
    by_facility: dict[str, float] = defaultdict(float)
    by_category: dict[tuple[int, str], float] = defaultdict(float)
    methodology_samples: list[dict[str, Any]] = []

    for emission, activity, facility, factor in rows:
        total_kg += emission.co2e_kg
        by_scope[emission.scope] += emission.co2e_kg
        by_facility[facility.name] += emission.co2e_kg
        by_category[(emission.scope, emission.category)] += emission.co2e_kg
        if len(methodology_samples) < 3 and factor is not None:
            methodology_samples.append(
                {
                    "scope": emission.scope,
                    "activity": activity.activity_description,
                    "quantity": activity.quantity,
                    "unit": activity.unit,
                    "factor_value": factor.factor_value,
                    "factor_unit": factor.unit,
                    "factor_source": factor.source,
                    "factor_year": factor.year,
                    "co2e_tonnes": emission.co2e_kg / KG_PER_TONNE,
                    "method": emission.calculation_method,
                }
            )

    # Facilities not just names — we want a full roster.
    facilities = list(db.scalars(select(Facility).where(Facility.org_id == org.id)).all())
    supplier_count = db.scalar(
        select(func.count(Supplier.id)).where(Supplier.org_id == org.id)
    ) or 0
    submission_count = db.scalar(
        select(func.count(SupplierSubmission.id))
        .join(Supplier, SupplierSubmission.supplier_id == Supplier.id)
        .where(Supplier.org_id == org.id)
        .where(SupplierSubmission.period.between(f"{start.year}-Q1", f"{end.year}-Q4"))
    ) or 0

    total_t = total_kg / KG_PER_TONNE
    scope_breakdown = sorted(
        [
            {
                "scope": s,
                "tonnes": v / KG_PER_TONNE,
                "pct": (v / total_kg * 100.0) if total_kg else 0.0,
            }
            for s, v in by_scope.items()
        ],
        key=lambda x: x["scope"],
    )
    facility_breakdown = sorted(
        [{"name": n, "tonnes": v / KG_PER_TONNE} for n, v in by_facility.items()],
        key=lambda x: x["tonnes"],
        reverse=True,
    )
    category_breakdown = sorted(
        [
            {"scope": s, "category": c, "tonnes": v / KG_PER_TONNE}
            for (s, c), v in by_category.items()
        ],
        key=lambda x: x["tonnes"],
        reverse=True,
    )[:10]

    return {
        "org": org,
        "period": period,
        "period_start": start,
        "period_end": end,
        "total_tonnes": total_t,
        "by_scope": scope_breakdown,
        "by_facility": facility_breakdown,
        "by_category": category_breakdown,
        "methodology_samples": methodology_samples,
        "facilities": facilities,
        "supplier_count": supplier_count,
        "submission_count": submission_count,
        "activity_row_count": len(rows),
    }


# ── Styles ────────────────────────────────────────────────────────────


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "t",
            parent=base["Title"],
            fontSize=22,
            leading=26,
            textColor=SLATE_900,
            spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "st",
            parent=base["Normal"],
            fontSize=11,
            textColor=SLATE_500,
            spaceAfter=18,
        ),
        "h1": ParagraphStyle(
            "h1",
            parent=base["Heading1"],
            fontSize=14,
            leading=18,
            textColor=BRAND_COLOR,
            spaceBefore=14,
            spaceAfter=6,
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=base["Heading2"],
            fontSize=11,
            leading=14,
            textColor=SLATE_900,
            spaceBefore=8,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["Normal"],
            fontSize=10,
            leading=14,
            textColor=SLATE_900,
        ),
        "muted": ParagraphStyle(
            "muted",
            parent=base["Normal"],
            fontSize=9,
            leading=12,
            textColor=SLATE_500,
        ),
    }


def _table_style() -> TableStyle:
    return TableStyle(
        [
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BACKGROUND", (0, 0), (-1, 0), SLATE_200),
            ("TEXTCOLOR", (0, 0), (-1, 0), SLATE_900),
            ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("LINEBELOW", (0, 0), (-1, 0), 0.5, SLATE_500),
            ("LINEBELOW", (0, -1), (-1, -1), 0.25, SLATE_200),
        ]
    )


# ── Framework-specific section layouts ────────────────────────────────


_FRAMEWORK_META: dict[Framework, dict[str, str]] = {
    "BRSR": {
        "standard": "SEBI BRSR (Business Responsibility & Sustainability Report)",
        "principle": "Principle 6 — Environment",
        "section_emissions": "Principle 6.7 — Greenhouse Gas Emissions",
        "section_methodology": "Principle 6 Assurance — Methodology & Emission Factors",
    },
    "GRI": {
        "standard": "GRI Standards — GRI 305: Emissions (2016)",
        "principle": "Material topic: Emissions",
        "section_emissions": "GRI 305-1/-2/-3 — Scope 1, 2, 3 Emissions",
        "section_methodology": "GRI 305 — Disclosure 305-1 c: Emission Factors & Consolidation",
    },
    "TCFD": {
        "standard": "TCFD — Task Force on Climate-related Financial Disclosures",
        "principle": "Pillar: Metrics & Targets",
        "section_emissions": "Metrics & Targets (b) — Scope 1, 2, 3 Emissions",
        "section_methodology": "Metrics & Targets (a) — Assessment Methodology",
    },
}


def _header_flowables(ctx: dict[str, Any], framework: Framework, s: dict[str, ParagraphStyle]) -> list:
    org = ctx["org"]
    meta = _FRAMEWORK_META[framework]
    return [
        Paragraph(f"{framework} — GHG Disclosure", s["title"]),
        Paragraph(
            f"{org.name} · {meta['standard']} · Period: {ctx['period']} "
            f"({ctx['period_start']:%d %b %Y} – {ctx['period_end']:%d %b %Y}) · "
            f"Generated {datetime.utcnow():%d %b %Y}",
            s["subtitle"],
        ),
    ]


def _summary_flowables(ctx: dict[str, Any], s: dict[str, ParagraphStyle]) -> list:
    out = [Paragraph("1. Executive summary", s["h1"])]
    out.append(
        Paragraph(
            f"Total GHG emissions in {ctx['period']}: "
            f"<b>{ctx['total_tonnes']:,.1f} tCO₂e</b> across "
            f"{len(ctx['facilities'])} operational facilities and {ctx['supplier_count']} "
            f"tier-1 suppliers. Based on {ctx['activity_row_count']} activity records "
            f"resolved through the CarbonLens emissions traceability chain.",
            s["body"],
        )
    )
    out.append(Spacer(1, 6))
    out.append(
        Paragraph(
            f"{ctx['supplier_count']} suppliers engaged · "
            f"{ctx['submission_count']} quarterly submissions received during reporting period.",
            s["muted"],
        )
    )
    return out


def _scope_table(ctx: dict[str, Any], framework: Framework, s: dict[str, ParagraphStyle]) -> list:
    meta = _FRAMEWORK_META[framework]
    header = [
        Paragraph("2. " + meta["section_emissions"], s["h1"]),
        Paragraph(
            "GHG emissions by scope, consolidated operational control basis. Values in tCO₂e.",
            s["muted"],
        ),
        Spacer(1, 6),
    ]
    rows = [["Scope", "Description", "tCO₂e", "% of total"]]
    scope_desc = {
        1: "Direct emissions (fuels, fleet, refrigerants)",
        2: "Indirect — purchased electricity, steam, heat",
        3: "Value chain — goods, transport, travel, etc.",
    }
    for row in ctx["by_scope"]:
        rows.append(
            [
                f"Scope {row['scope']}",
                scope_desc.get(row["scope"], "—"),
                f"{row['tonnes']:,.1f}",
                f"{row['pct']:.1f}%",
            ]
        )
    rows.append(["Total", "", f"{ctx['total_tonnes']:,.1f}", "100.0%"])
    table = Table(rows, colWidths=[25 * mm, 80 * mm, 30 * mm, 25 * mm])
    style = _table_style()
    style.add("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold")
    style.add("LINEABOVE", (0, -1), (-1, -1), 0.5, SLATE_500)
    table.setStyle(style)
    return header + [table]


def _facility_table(ctx: dict[str, Any], s: dict[str, ParagraphStyle]) -> list:
    header = [
        Paragraph("3. Emissions by facility", s["h1"]),
        Paragraph(
            "Breakdown by operational site. Used for intensity and site-level target setting.",
            s["muted"],
        ),
        Spacer(1, 6),
    ]
    rows = [["Facility", "tCO₂e", "% of total"]]
    total = ctx["total_tonnes"]
    for row in ctx["by_facility"]:
        pct = (row["tonnes"] / total * 100.0) if total else 0.0
        rows.append([row["name"], f"{row['tonnes']:,.1f}", f"{pct:.1f}%"])
    table = Table(rows, colWidths=[80 * mm, 40 * mm, 25 * mm])
    table.setStyle(_table_style())
    return header + [table]


def _category_table(ctx: dict[str, Any], s: dict[str, ParagraphStyle]) -> list:
    header = [
        Paragraph("4. Top emission categories", s["h1"]),
        Paragraph(
            "Largest 10 categories across all scopes. Drives mitigation priority.",
            s["muted"],
        ),
        Spacer(1, 6),
    ]
    rows = [["Scope", "Category", "tCO₂e"]]
    for row in ctx["by_category"]:
        rows.append([f"S{row['scope']}", row["category"], f"{row['tonnes']:,.1f}"])
    table = Table(rows, colWidths=[20 * mm, 90 * mm, 35 * mm])
    table.setStyle(_table_style())
    return header + [table]


def _methodology_flowables(
    ctx: dict[str, Any], framework: Framework, s: dict[str, ParagraphStyle]
) -> list:
    meta = _FRAMEWORK_META[framework]
    out = [
        Paragraph("5. " + meta["section_methodology"], s["h1"]),
        Paragraph(
            "Every emission figure in this report is produced as quantity × emission factor. "
            "Factors are resolved in priority order: exact (category+subcategory+region+year) → "
            "most-recent regional match → global default. Sample calculations below demonstrate "
            "the traceability chain.",
            s["body"],
        ),
        Spacer(1, 6),
    ]
    if not ctx["methodology_samples"]:
        out.append(Paragraph("No factor-linked emissions in this period.", s["muted"]))
        return out

    rows = [["Activity", "Qty × factor", "Factor source", "tCO₂e"]]
    for sample in ctx["methodology_samples"]:
        rows.append(
            [
                Paragraph(f"S{sample['scope']} · {sample['activity']}", s["muted"]),
                f"{sample['quantity']:g} {sample['unit']} × "
                f"{sample['factor_value']:g} {sample['factor_unit']}",
                f"{sample['factor_source']} ({sample['factor_year']})",
                f"{sample['co2e_tonnes']:,.2f}",
            ]
        )
    table = Table(rows, colWidths=[55 * mm, 50 * mm, 35 * mm, 25 * mm])
    table.setStyle(_table_style())
    out.append(table)
    return out


def _narrative_flowables(narrative: str | None, s: dict[str, ParagraphStyle]) -> list:
    if not narrative:
        return []
    out = [
        PageBreak(),
        Paragraph("6. AI-written executive narrative", s["h1"]),
        Paragraph(
            "Plain-English summary generated from the numbers above. Included at the "
            "preparer's discretion — not part of the framework disclosure requirement.",
            s["muted"],
        ),
        Spacer(1, 8),
    ]
    for para in narrative.strip().split("\n"):
        if para.strip():
            out.append(Paragraph(para.strip(), s["body"]))
            out.append(Spacer(1, 4))
    return out


# ── Orchestration ─────────────────────────────────────────────────────


def render_pdf(
    *,
    framework: Framework,
    period: str,
    context: dict[str, Any],
    narrative: str | None,
    report_id: int,
) -> Path:
    """Render a PDF to `PDF_OUTPUT_DIR` and return the absolute path."""
    out_dir = settings.pdf_output_path
    out_dir.mkdir(parents=True, exist_ok=True)
    path = (out_dir / f"{framework.lower()}_{period}_{report_id}.pdf").resolve()

    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"{framework} GHG Disclosure — {context['period']}",
        author="CarbonLens",
    )

    s = _styles()
    flowables: list = []
    flowables += _header_flowables(context, framework, s)
    flowables += _summary_flowables(context, s)
    flowables += [Spacer(1, 4)] + _scope_table(context, framework, s)
    flowables += [Spacer(1, 4)] + _facility_table(context, s)
    flowables += [Spacer(1, 4)] + _category_table(context, s)
    flowables += [Spacer(1, 4)] + _methodology_flowables(context, framework, s)
    flowables += _narrative_flowables(narrative, s)
    flowables += [
        Spacer(1, 12),
        Paragraph(
            "Generated by CarbonLens. Every figure above resolves through the emissions "
            "traceability chain (activity_data → emissions → emission_factors). "
            "Methodology is auditable row-by-row via the platform's /emissions/{id}/methodology endpoint.",
            s["muted"],
        ),
    ]
    doc.build(flowables)
    return path
