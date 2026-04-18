from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AnchorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    report_id: int
    merkle_root: str
    chain: str
    tx_hash: str | None
    block_number: int | None
    sealed_by: str
    sealed_at: datetime


class SealResponse(BaseModel):
    anchor: AnchorOut
    manifest: dict[str, Any]


class ChainAnchorResponse(BaseModel):
    anchor: AnchorOut
    explorer_url: str | None


class VerifyResponse(BaseModel):
    verified: bool
    diverged_subtree: str | None
    stored_root: str
    recomputed_root: str
    stored_manifest: dict[str, Any]
    recomputed_manifest: dict[str, Any]
    sealed_at: datetime
    sealed_by: str
    chain: str
    tx_hash: str | None
    block_number: int | None
