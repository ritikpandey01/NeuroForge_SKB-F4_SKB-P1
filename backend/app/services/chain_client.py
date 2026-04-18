"""Blockchain anchoring client for CarbonLens.

Submits a 32-byte Merkle root + (org_id, period) tuple to the
`CarbonLensAnchor` smart contract on Polygon. Two modes:

* **simulated** — no RPC is touched. A deterministic fake tx hash is
  generated from the inputs + server time. Used in demo mode so the
  platform runs end-to-end without a funded wallet. Chain name is
  returned as "polygon-simulated" so a reader can't mistake it for
  the real thing.
* **polygon / polygon-amoy** — real tx submitted via web3.py. Requires
  `POLYGON_RPC_URL`, `ANCHOR_CONTRACT_ADDRESS`, and
  `ANCHOR_PRIVATE_KEY` to be set. The key must hold enough MATIC to
  pay gas (~$0.01 per anchor).

The handler treats mode as the single source of truth; never fall back
silently from real → simulated (that would mislead the caller).
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass

from app.core.config import settings


class ChainError(Exception):
    """Any failure submitting an anchor — network, gas, signing, revert."""


@dataclass
class AnchorReceipt:
    chain: str  # polygon | polygon-amoy | polygon-simulated
    tx_hash: str
    block_number: int
    explorer_url: str | None  # link to PolygonScan page for this tx, if known


_ANCHOR_ABI = [
    {
        "inputs": [
            {"internalType": "uint256", "name": "orgId", "type": "uint256"},
            {"internalType": "string", "name": "period", "type": "string"},
            {"internalType": "bytes32", "name": "h", "type": "bytes32"},
        ],
        "name": "anchor",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "uint256",
                "name": "orgId",
                "type": "uint256",
            },
            {"indexed": False, "internalType": "string", "name": "period", "type": "string"},
            {"indexed": False, "internalType": "bytes32", "name": "hash", "type": "bytes32"},
            {"indexed": False, "internalType": "uint256", "name": "ts", "type": "uint256"},
        ],
        "name": "Anchor",
        "type": "event",
    },
]


def _normalize_hex_root(root: str) -> bytes:
    r = root[2:] if root.startswith("0x") else root
    if len(r) != 64:
        raise ChainError(f"merkle root must be 32 bytes, got {len(r)//2} bytes")
    return bytes.fromhex(r)


def _simulated_anchor(org_id: int, period: str, root: str) -> AnchorReceipt:
    """Deterministic-but-plausible fake receipt for demo mode.

    The tx hash is sha256(mode || org_id || period || root || unix_ts)
    so a single anchor always looks unique, but no RPC is called."""
    payload = f"sim|{org_id}|{period}|{root}|{int(time.time())}"
    tx = "0x" + hashlib.sha256(payload.encode()).hexdigest()
    # Approximate "current" Amoy block number — cosmetic only.
    block = 20_000_000 + int(time.time() % 1_000_000)
    return AnchorReceipt(
        chain="polygon-simulated",
        tx_hash=tx,
        block_number=block,
        explorer_url=None,
    )


def _real_anchor(org_id: int, period: str, root: str) -> AnchorReceipt:
    """Submit anchor tx to Polygon. Requires web3.py + env config."""
    missing = [
        k
        for k in (
            "POLYGON_RPC_URL",
            "ANCHOR_CONTRACT_ADDRESS",
            "ANCHOR_PRIVATE_KEY",
        )
        if not getattr(settings, k)
    ]
    if missing:
        raise ChainError(
            f"real-chain mode requires: {', '.join(missing)}. "
            f"Either set these in .env or switch CHAIN_MODE=simulated."
        )

    try:
        from web3 import Web3
        from web3.middleware import geth_poa_middleware  # type: ignore[attr-defined]
    except ImportError as e:  # pragma: no cover
        raise ChainError(
            "web3 is not installed. Run `pip install web3` to enable real anchoring."
        ) from e

    w3 = Web3(Web3.HTTPProvider(settings.POLYGON_RPC_URL))
    # Polygon uses PoA — inject the middleware so headers parse correctly.
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    if not w3.is_connected():
        raise ChainError(f"cannot reach Polygon RPC at {settings.POLYGON_RPC_URL}")

    acct = w3.eth.account.from_key(settings.ANCHOR_PRIVATE_KEY)
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(settings.ANCHOR_CONTRACT_ADDRESS),
        abi=_ANCHOR_ABI,
    )

    nonce = w3.eth.get_transaction_count(acct.address)
    try:
        txn = contract.functions.anchor(
            org_id, period, _normalize_hex_root(root)
        ).build_transaction(
            {
                "from": acct.address,
                "nonce": nonce,
                "chainId": settings.ANCHOR_CHAIN_ID,
                # gas estimate is left to web3; caller can override by
                # pre-flight estimateGas if needed
            }
        )
    except Exception as e:
        raise ChainError(f"tx build failed: {e}") from e

    signed = acct.sign_transaction(txn)
    try:
        tx_hash_bytes = w3.eth.send_raw_transaction(signed.rawTransaction)
    except Exception as e:
        raise ChainError(f"tx broadcast failed: {e}") from e

    try:
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash_bytes, timeout=180)
    except Exception as e:
        raise ChainError(f"tx did not confirm within 180s: {e}") from e

    if receipt.status != 1:
        raise ChainError(f"tx reverted: {tx_hash_bytes.hex()}")

    chain_name = (
        "polygon-amoy"
        if settings.ANCHOR_CHAIN_ID == 80002
        else "polygon"
        if settings.ANCHOR_CHAIN_ID == 137
        else f"chain-{settings.ANCHOR_CHAIN_ID}"
    )
    tx_hash_hex = tx_hash_bytes.hex()
    explorer = (
        f"{settings.ANCHOR_EXPLORER_URL}/tx/{tx_hash_hex}"
        if settings.ANCHOR_EXPLORER_URL
        else None
    )
    return AnchorReceipt(
        chain=chain_name,
        tx_hash=tx_hash_hex if tx_hash_hex.startswith("0x") else f"0x{tx_hash_hex}",
        block_number=receipt.blockNumber,
        explorer_url=explorer,
    )


def submit_anchor(org_id: int, period: str, root: str) -> AnchorReceipt:
    """Submit a Merkle root to the configured chain.

    Routes by CHAIN_MODE. Raises ChainError on any failure — the caller
    should catch and surface a 502 (upstream) or 503 (not configured)."""
    mode = settings.CHAIN_MODE.lower()
    if mode == "simulated":
        return _simulated_anchor(org_id, period, root)
    if mode in ("polygon", "polygon-amoy"):
        return _real_anchor(org_id, period, root)
    raise ChainError(f"unknown CHAIN_MODE: {settings.CHAIN_MODE}")
