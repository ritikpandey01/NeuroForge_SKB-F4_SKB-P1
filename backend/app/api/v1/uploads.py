from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from openai import APIError
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.api.scoping import ensure_facility
from app.core.llm_client import CircuitBreakerOpen, LLMNotConfigured
from app.db.models import ActivityData, User, UserRole
from app.db.session import get_db
from app.services.calculation_engine import calculate_for_activity
from app.services.csv_parser import parse_csv
from app.services.document_parser import (
    ACCEPTED_MIME_TYPES,
    DOC_TYPE_HINTS,
    parse_document,
)

router = APIRouter(prefix="/uploads")

MAX_BYTES = 5 * 1024 * 1024  # 5 MB cap on a single CSV upload
MAX_DOC_BYTES = 10 * 1024 * 1024  # 10 MB cap on document uploads (PDF/image)


@router.post("/csv/preview")
async def preview_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin, UserRole.analyst)),
) -> dict:
    """Parse + validate a CSV without writing to the DB. Returns preview rows."""
    body = await file.read()
    if len(body) > MAX_BYTES:
        raise HTTPException(413, f"file too large ({len(body)} bytes, max {MAX_BYTES})")
    if not body:
        raise HTTPException(400, "empty file")

    result = parse_csv(db, file_bytes=body, uploaded_by=user.email, org_id=user.org_id)
    return {"filename": file.filename, **result.to_dict()}


class CommitRow(BaseModel):
    facility_id: int
    scope: int
    category: str
    subcategory: str
    activity_description: str
    quantity: float
    unit: str
    period_start: date
    period_end: date
    source_document: str | None = None
    data_quality_score: int = 3


class CommitRequest(BaseModel):
    rows: list[CommitRow]


@router.post("/csv/commit")
def commit_csv(
    payload: CommitRequest,
    auto_calculate: bool = Query(True),
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin, UserRole.analyst)),
) -> dict:
    """Persist a list of pre-validated rows (typically the 'rows_ready' subset
    returned by /csv/preview, optionally edited by the user)."""
    for row in payload.rows:
        ensure_facility(db, row.facility_id, user.org_id)

    inserted: list[int] = []
    calc_errors: list[dict] = []

    for row in payload.rows:
        activity = ActivityData(**row.model_dump(), uploaded_by=user.email)
        db.add(activity)
        db.flush()
        inserted.append(activity.id)

        if auto_calculate:
            sp = db.begin_nested()
            try:
                calculate_for_activity(db, activity)
                sp.commit()
            except Exception as e:
                sp.rollback()
                calc_errors.append({"activity_id": activity.id, "error": str(e)})

    db.commit()
    return {
        "inserted": len(inserted),
        "activity_ids": inserted,
        "calc_errors": calc_errors,
    }


@router.post("/document/preview")
async def preview_document(
    file: UploadFile = File(...),
    doc_type: str | None = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin, UserRole.analyst)),
) -> dict:
    """Run the AI document parser against an uploaded PDF/image. Returns rows
    in the same shape as `/csv/preview` so the existing `/csv/commit` endpoint
    can ingest the user-confirmed subset.

    `doc_type` is an optional hint — when set, the parser prepends a targeted
    extraction block (expected category/subcategory/unit) to the prompt.
    Accepted keys: see `GET /uploads/document/types`.
    """
    body = await file.read()
    if len(body) > MAX_DOC_BYTES:
        raise HTTPException(
            413, f"file too large ({len(body)} bytes, max {MAX_DOC_BYTES})"
        )
    if not body:
        raise HTTPException(400, "empty file")

    mime_type = (file.content_type or "").lower()
    if mime_type not in ACCEPTED_MIME_TYPES:
        raise HTTPException(
            415,
            f"unsupported content-type '{mime_type}'. "
            f"Accepted: {sorted(ACCEPTED_MIME_TYPES)}",
        )

    if doc_type and doc_type != "auto" and doc_type not in DOC_TYPE_HINTS:
        raise HTTPException(
            422,
            f"unknown doc_type '{doc_type}'. Accepted: "
            f"'auto' or one of {sorted(DOC_TYPE_HINTS)}",
        )

    try:
        result = parse_document(
            db,
            file_bytes=body,
            mime_type=mime_type,
            filename=file.filename,
            uploaded_by=user.email,
            doc_type=doc_type if doc_type and doc_type != "auto" else None,
            org_id=user.org_id,
        )
    except LLMNotConfigured as e:
        raise HTTPException(503, str(e)) from e
    except CircuitBreakerOpen as e:
        raise HTTPException(503, str(e)) from e
    except APIError as e:
        upstream = getattr(e, "message", None) or str(e)
        raise HTTPException(status_code=502, detail=f"LLM upstream: {upstream}") from e

    return {"filename": file.filename, **result.to_dict()}


@router.get("/document/types", response_model=None)
def document_types(
    _user: User = Depends(get_current_user),
) -> dict:
    """Returns the valid `doc_type` keys for `/uploads/document/preview` along
    with the targeting hint each one applies. The UI uses this to populate the
    document-type dropdown."""
    return {
        "types": [
            {"key": key, "hint": hint}
            for key, hint in DOC_TYPE_HINTS.items()
        ]
    }


@router.get("/csv/template", response_model=None)
def csv_template(
    _user: User = Depends(get_current_user),
) -> dict:
    """Returns the expected CSV schema so the UI can show a template/help."""
    return {
        "required_columns": [
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
        "optional_columns": ["source_document", "data_quality_score"],
        "example_row": {
            "facility_name": "Mumbai HQ Office",
            "scope": 2,
            "category": "Electricity",
            "subcategory": "Grid Electricity",
            "activity_description": "Office grid electricity consumption",
            "quantity": 18500,
            "unit": "kWh",
            "period_start": "2024-01-01",
            "period_end": "2024-01-31",
            "source_document": "MSEB-INV-2024-01",
            "data_quality_score": 4,
        },
    }
