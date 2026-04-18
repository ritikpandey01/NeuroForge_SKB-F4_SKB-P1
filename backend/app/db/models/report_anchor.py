from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.report import Report


class ReportAnchor(Base):
    """Cryptographic anchor for a generated report.

    One row per seal/anchor attempt. `merkle_root` is the hex-encoded
    sha256 Merkle root covering activity rows + factor versions + evidence
    manifest + methodology snapshot + PDF bytes. `chain="local"` means the
    root is only stored here (Phase 1 tamper-evidence). A real on-chain
    anchor flips `chain` to "polygon" / "polygon-amoy" and fills
    `tx_hash` + `block_number`.
    """

    __tablename__ = "report_anchors"

    id: Mapped[int] = mapped_column(primary_key=True)
    report_id: Mapped[int] = mapped_column(
        ForeignKey("reports.id", ondelete="CASCADE"), index=True
    )
    org_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    merkle_root: Mapped[str] = mapped_column(String(66))  # "0x" + 64 hex
    manifest: Mapped[str] = mapped_column(Text)  # JSON: per-subtree roots + leaf counts
    chain: Mapped[str] = mapped_column(String(30), default="local")
    tx_hash: Mapped[str | None] = mapped_column(String(80), nullable=True)
    block_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sealed_by: Mapped[str] = mapped_column(String(200))
    sealed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    report: Mapped["Report"] = relationship()
