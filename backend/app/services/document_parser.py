"""AI document parser (Module 6).

Takes a bill / invoice / utility statement (PDF or image), asks the LLM
(OpenAI gpt-4o-mini by default) to extract activity-data rows in the same
shape `services/csv_parser.py` produces, then re-resolves facilities and
re-runs validation locally so the final preview is byte-compatible with
`/uploads/csv/preview`. The frontend's confirm-and-edit flow and
`/uploads/csv/commit` endpoint are reused as-is.

Why not let the model return facility_ids? Because it has no DB access. We
hand it the list of facility names; it returns a name; we resolve it
server-side. Same trick keeps emission factor selection out of the prompt.

PDFs: rendered page-by-page to PNG via PyMuPDF, then handed to the chat
vision endpoint as data URIs. Capped at `DOC_MAX_PAGES`. A typical utility
bill is one page; invoices with many line items may span 2-3.
"""

from __future__ import annotations

import base64
import calendar
import json
from dataclasses import dataclass
from datetime import date

import fitz  # PyMuPDF
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.llm_client import llm
from app.db.models import Facility
from app.services.validation import validate_activity

ACCEPTED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/webp",
}


# Optional doc-type hints. When the user picks one in the UI, we prepend a short
# targeting block to the user message so the model knows which fields on the page
# to prioritise. Keys stay stable; UI labels live in the frontend. `auto` = no hint.
DOC_TYPE_HINTS: dict[str, str] = {
    "electricity_bill": (
        "Document type: ELECTRICITY BILL (grid supply). "
        "Expect: consumer/account number, billing period, sanctioned load, "
        "active-energy kWh reading. "
        "Output: scope=2, category='electricity', subcategory='grid_india' "
        "(or grid_uk/grid_usa based on utility). Quantity = active-energy kWh "
        "(NOT kVArh, NOT the rupee amount). Unit='kWh'."
    ),
    "fuel_invoice": (
        "Document type: FUEL INVOICE (diesel / petrol / LPG). "
        "Expect: tanker deliveries, DC numbers, litres per delivery, total litres. "
        "Output: scope=1, category='fuel', subcategory matches the product "
        "(diesel/petrol/lpg/kerosene/furnace_oil). Quantity = total litres delivered. "
        "Unit='litre'. Sum multiple deliveries into one row per invoice."
    ),
    "natural_gas_bill": (
        "Document type: NATURAL GAS / PNG BILL. "
        "Expect: meter opening/closing reading, volume consumed in m³, "
        "calorific-value line. "
        "Output: scope=1, category='fuel', subcategory='natural_gas'. "
        "Quantity = volume consumed. Unit='m3'. Do NOT convert to GJ unless "
        "the meter is volumeless."
    ),
    "material_purchase": (
        "Document type: MATERIAL PURCHASE INVOICE "
        "(steel / aluminium / cement / copper / plastic / chemicals). "
        "Expect: HSN code, material grade, net weight in MT or kg. "
        "Output: scope=3, category='material', subcategory matches the material "
        "(steel/aluminium/cement/copper/plastics_general/etc). "
        "Quantity = net delivered weight in kg (convert MT → kg, 1 MT = 1000 kg). "
        "Unit='kg'. Emit ONE row per distinct material line."
    ),
    "freight_invoice": (
        "Document type: FREIGHT / LOGISTICS INVOICE (3rd-party carrier). "
        "Expect: LR numbers, origin→destination, distance km, cargo weight, "
        "sometimes tonne-km already calculated. "
        "Output: scope=3, category='freight', subcategory based on mode "
        "(road_hgv / road_lcv / rail / sea_container / air_freight). "
        "Quantity = total tonne-km (= km × tonnes; sum across LRs). Unit='tonne-km'."
    ),
    "travel_itinerary": (
        "Document type: BUSINESS TRAVEL ITINERARY (airline / rail / taxi). "
        "Expect: flight segments, sectors, passenger count, distance km per segment. "
        "Output: scope=3, category='travel', subcategory matches mode "
        "(flight_domestic / flight_international / flight_short_haul / train_domestic / taxi). "
        "Quantity = total passenger-km (= segment km × pax; sum across segments). "
        "Unit='passenger-km'."
    ),
    "waste_disposal": (
        "Document type: WASTE DISPOSAL RECEIPT. "
        "Expect: multiple waste streams (landfill / recycled / incinerated / composted), "
        "quantity per stream in kg. "
        "Output: scope=3, category='waste', subcategory per stream "
        "(landfill_mixed / recycled_mixed / incinerated / composted). "
        "Emit ONE row per treatment path. Quantity in kg. Unit='kg'."
    ),
    "supplier_disclosure": (
        "Document type: SUPPLIER EMISSIONS DISCLOSURE (NOT a line-item invoice). "
        "These are already-aggregated totals at the supplier level. "
        "IMPORTANT: do NOT extract these as your own activity data — they belong "
        "in the supplier-submissions workflow, not the activity ledger. Return "
        "zero rows and put an explanatory note in `warnings`."
    ),
}


SYSTEM_PROMPT = """You are an emissions-data extraction assistant for CarbonLens, a corporate GHG accounting platform. Your job is to read utility bills, fuel invoices, supplier statements, freight bills, and similar source documents, and emit structured activity-data rows ready to be ingested into a Scope 1/2/3 ledger.

Output rules — NON-NEGOTIABLE:
  - Always invoke the `record_activities` tool exactly once. Never reply in plain text.
  - One row per distinct billing line. If a single bill covers two months or two meters, emit two rows.
  - `quantity` is the consumed amount in the listed `unit` (NOT the monetary cost). Round to at most 4 decimals.
  - `unit` must be the actual physical unit on the document: kWh, MWh, litre, m3, kg, tonne, km, tonne-km, GJ, etc. Preserve singular form.
  - `period_start` / `period_end` are ISO `YYYY-MM-DD`. If only a month is shown (e.g., "March 2024"), use the first and last day of that month.
  - `facility_name` MUST match — case-insensitively — one of the facility names provided in the user message. If you cannot match confidently, still emit the row but put your best guess in `facility_name` and add an entry to `warnings` explaining the mismatch.
  - Pick `scope` per the GHG Protocol:
      Scope 1 = direct combustion the org operates (diesel in own genset, natural gas in own boiler, refrigerant top-up, owned-vehicle fuel).
      Scope 2 = purchased grid electricity, district steam/heat/cooling.
      Scope 3 = upstream/downstream — purchased materials (steel, cement), transport by 3rd parties, business travel, employee commuting, waste disposal, supplier emissions.
  - `data_quality_score` (1=poor, 5=excellent): 5 = direct meter read with itemized invoice, 4 = invoice without meter detail, 3 = monthly summary, 2 = estimated/derived, 1 = back-of-envelope.
  - `source_document` should be a short identifier from the document itself (invoice #, meter ID, supplier name + month). Falls back to filename if nothing else is on the page.
  - If a value is illegible, ambiguous, or only partially shown, DO NOT GUESS A NUMBER. Skip that row and add an entry to `warnings`.
  - `extraction_notes` (per row): one short sentence explaining where you found the number (e.g., "Total kWh from the 'Energy charges' row, page 2"). Optional but encouraged.
  - `document_summary`: one sentence describing what the document is (e.g., "MSEB electricity bill for Mumbai HQ, March 2024 billing period").
"""


@dataclass
class DocumentParseResult:
    rows: list[dict]
    summary: dict
    document_summary: str | None
    model_warnings: list[str]

    def to_dict(self) -> dict:
        return {
            "summary": self.summary,
            "rows": self.rows,
            "document_summary": self.document_summary,
            "model_warnings": self.model_warnings,
        }


def _facility_directory(
    db: Session, *, org_id: int | None = None
) -> tuple[dict[str, Facility], str]:
    stmt = select(Facility)
    if org_id is not None:
        stmt = stmt.where(Facility.org_id == org_id)
    facilities = db.scalars(stmt).all()
    lookup = {f.name.strip().lower(): f for f in facilities}
    listing = "\n".join(
        f"  - {f.name} (type: {f.type}, location: {f.location}, country: {f.country})"
        for f in facilities
    )
    return lookup, listing


def _record_activities_tool() -> dict:
    return {
        "type": "function",
        "function": {
            "name": "record_activities",
            "description": (
                "Emit one or more activity-data rows extracted from the document. "
                "Call this exactly once per document, with all rows you found."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "document_summary": {
                        "type": "string",
                        "description": "One-sentence description of the document.",
                    },
                    "rows": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "facility_name": {"type": "string"},
                                "scope": {"type": "integer", "enum": [1, 2, 3]},
                                "category": {"type": "string"},
                                "subcategory": {"type": "string"},
                                "activity_description": {"type": "string"},
                                "quantity": {"type": "number", "minimum": 0},
                                "unit": {"type": "string"},
                                "period_start": {
                                    "type": "string",
                                    "description": "ISO YYYY-MM-DD",
                                },
                                "period_end": {
                                    "type": "string",
                                    "description": "ISO YYYY-MM-DD",
                                },
                                "source_document": {"type": "string"},
                                "data_quality_score": {
                                    "type": "integer",
                                    "minimum": 1,
                                    "maximum": 5,
                                },
                                "extraction_notes": {"type": "string"},
                            },
                            "required": [
                                "facility_name",
                                "scope",
                                "category",
                                "subcategory",
                                "activity_description",
                                "quantity",
                                "unit",
                                "period_start",
                                "period_end",
                            ],
                        },
                    },
                    "warnings": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Document-level issues (missing facility match, illegible values, etc.).",
                    },
                },
                "required": ["rows"],
            },
        },
    }


def _render_pdf_pages(pdf_bytes: bytes, *, max_pages: int, dpi: int) -> list[bytes]:
    """Render a PDF to a list of PNG byte-strings, one per page."""
    pages: list[bytes] = []
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for i, page in enumerate(doc):
            if i >= max_pages:
                break
            pix = page.get_pixmap(dpi=dpi)
            pages.append(pix.tobytes("png"))
    return pages


def _image_blocks(file_bytes: bytes, mime_type: str) -> list[dict]:
    """Return chat-completion `image_url` content blocks (one per rendered page)."""
    if mime_type == "application/pdf":
        pngs = _render_pdf_pages(
            file_bytes,
            max_pages=settings.DOC_MAX_PAGES,
            dpi=settings.DOC_RENDER_DPI,
        )
        return [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{base64.b64encode(p).decode('ascii')}",
                    "detail": "high",
                },
            }
            for p in pngs
        ]
    # Raster image: pass through as-is.
    b64 = base64.b64encode(file_bytes).decode("ascii")
    return [
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:{mime_type};base64,{b64}",
                "detail": "high",
            },
        }
    ]


def _parse_date(value: str, *, end_of_month: bool = False) -> date:
    s = value.strip()
    if len(s) == 7 and s[4] == "-":
        y, m = int(s[:4]), int(s[5:])
        if end_of_month:
            return date(y, m, calendar.monthrange(y, m)[1])
        return date(y, m, 1)
    return date.fromisoformat(s)


def _materialize(
    db: Session,
    *,
    facility_lookup: dict[str, Facility],
    extracted: list[dict],
    uploaded_by: str | None,
    fallback_source: str | None,
) -> list[dict]:
    out: list[dict] = []
    for idx, ex in enumerate(extracted, start=1):
        issues: list[dict] = []
        raw = dict(ex)
        parsed = None

        try:
            facility_name = str(ex.get("facility_name", "")).strip()
            facility = facility_lookup.get(facility_name.lower())
            if not facility:
                issues.append(
                    {
                        "severity": "error",
                        "field": "facility_name",
                        "message": f"unknown facility '{facility_name}' (rename to one of the seeded facilities, then re-commit)",
                    }
                )

            scope = int(ex["scope"])
            quantity = float(ex["quantity"])
            period_start = _parse_date(str(ex["period_start"]))
            period_end = _parse_date(str(ex["period_end"]), end_of_month=True)
            dq_raw = ex.get("data_quality_score")
            dq = int(dq_raw) if dq_raw not in (None, "") else 3

            if facility:
                v = validate_activity(
                    db,
                    facility_id=facility.id,
                    scope=scope,
                    category=str(ex.get("category", "")),
                    subcategory=str(ex.get("subcategory", "")),
                    quantity=quantity,
                    unit=str(ex.get("unit", "")),
                    period_start=period_start,
                    period_end=period_end,
                )
                issues.extend(
                    {"severity": i.severity, "field": i.field, "message": i.message}
                    for i in v.issues
                )

                parsed = {
                    "facility_id": facility.id,
                    "scope": scope,
                    "category": str(ex.get("category", "")),
                    "subcategory": str(ex.get("subcategory", "")),
                    "activity_description": str(ex.get("activity_description", "")),
                    "quantity": quantity,
                    "unit": str(ex.get("unit", "")),
                    "period_start": period_start.isoformat(),
                    "period_end": period_end.isoformat(),
                    "source_document": str(
                        ex.get("source_document") or fallback_source or ""
                    )
                    or None,
                    "data_quality_score": dq,
                    "uploaded_by": uploaded_by,
                }

            note = ex.get("extraction_notes")
            if note:
                issues.append(
                    {"severity": "info", "field": "extraction", "message": str(note)}
                )

        except (ValueError, KeyError, TypeError) as e:
            parsed = None
            issues.append(
                {
                    "severity": "error",
                    "field": "row",
                    "message": f"could not parse extracted row: {e}",
                }
            )

        out.append({"row_number": idx, "raw": raw, "parsed": parsed, "issues": issues})
    return out


def parse_document(
    db: Session,
    *,
    file_bytes: bytes,
    mime_type: str,
    filename: str | None = None,
    uploaded_by: str | None = None,
    doc_type: str | None = None,
    org_id: int | None = None,
) -> DocumentParseResult:
    if mime_type not in ACCEPTED_MIME_TYPES:
        raise ValueError(
            f"unsupported mime type '{mime_type}'. Accepted: {sorted(ACCEPTED_MIME_TYPES)}"
        )

    facility_lookup, facility_block = _facility_directory(db, org_id=org_id)

    hint = DOC_TYPE_HINTS.get(doc_type or "", "").strip()
    hint_block = f"\n\nUSER-PROVIDED HINT — trust this:\n{hint}\n" if hint else ""

    user_text = (
        "Extract every activity-data row you can find in the attached document."
        f"{hint_block}\n\n"
        "The known facilities (match case-insensitively):\n"
        f"{facility_block}\n\n"
        f"Filename: {filename or 'unknown'}"
    )

    image_blocks = _image_blocks(file_bytes, mime_type)

    response = llm.chat_completions_create(
        model=settings.OPENAI_MODEL,
        max_tokens=settings.OPENAI_MAX_TOKENS,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_text},
                    *image_blocks,
                ],
            },
        ],
        tools=[_record_activities_tool()],
        tool_choice={"type": "function", "function": {"name": "record_activities"}},
    )

    tool_input = _extract_tool_input(response)
    extracted_rows = tool_input.get("rows") or []
    document_summary = tool_input.get("document_summary")
    model_warnings = list(tool_input.get("warnings") or [])

    materialized = _materialize(
        db,
        facility_lookup=facility_lookup,
        extracted=extracted_rows,
        uploaded_by=uploaded_by,
        fallback_source=filename,
    )

    summary = {
        "total_rows": len(materialized),
        "rows_with_errors": sum(
            1 for r in materialized if any(i["severity"] == "error" for i in r["issues"])
        ),
        "rows_with_warnings": sum(
            1
            for r in materialized
            if any(i["severity"] == "warning" for i in r["issues"])
        ),
        "rows_ready": sum(
            1
            for r in materialized
            if r["parsed"] is not None
            and not any(i["severity"] == "error" for i in r["issues"])
        ),
    }

    return DocumentParseResult(
        rows=materialized,
        summary=summary,
        document_summary=document_summary,
        model_warnings=model_warnings,
    )


def _extract_tool_input(response) -> dict:
    """Pull the `record_activities` tool_call arguments from the SDK response.

    OpenAI's chat.completions returns:
        response.choices[0].message.tool_calls[i].function.{name, arguments(JSON string)}
    """
    try:
        choice = response.choices[0]
        tool_calls = getattr(choice.message, "tool_calls", None) or []
        for tc in tool_calls:
            fn = getattr(tc, "function", None)
            if fn and getattr(fn, "name", "") == "record_activities":
                args = getattr(fn, "arguments", None)
                if isinstance(args, str):
                    try:
                        return json.loads(args)
                    except json.JSONDecodeError:
                        return {}
                if isinstance(args, dict):
                    return args
    except (AttributeError, IndexError):
        pass
    return {}
