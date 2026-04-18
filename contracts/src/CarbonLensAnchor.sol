// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title CarbonLensAnchor
/// @notice Append-only registry of Merkle roots for ESG/GHG reports.
/// @dev The contract stores nothing about the underlying data — only a
///      32-byte commitment per (org, period). Verification is off-chain:
///      a reader recomputes the Merkle tree from current DB state and
///      compares the root to the one logged here. Divergence = tamper.
///
///      Gas footprint per anchor on Polygon PoS is ~30-40k gas
///      (~USD 0.001-0.01 at typical prices).
contract CarbonLensAnchor {
    address public immutable owner;

    /// @dev org_id => period => merkle root. Non-zero means "anchored".
    mapping(uint256 => mapping(string => bytes32)) public roots;
    mapping(uint256 => mapping(string => uint256)) public anchoredAt;

    event Anchor(uint256 indexed orgId, string period, bytes32 hash, uint256 ts);

    error NotOwner();
    error AlreadyAnchored(uint256 orgId, string period, bytes32 existing);
    error EmptyRoot();

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    /// @notice Record a Merkle root for a report. Reverts if the same
    ///         (orgId, period) pair was already anchored — re-anchoring
    ///         would let an attacker silently replace a prior commitment.
    /// @param orgId  CarbonLens internal organization ID
    /// @param period Reporting period string (e.g. "FY2023", "Q2-2024")
    /// @param h      32-byte Merkle root over activity/factor/evidence/methodology/PDF
    function anchor(uint256 orgId, string calldata period, bytes32 h) external onlyOwner {
        if (h == bytes32(0)) revert EmptyRoot();
        bytes32 existing = roots[orgId][period];
        if (existing != bytes32(0)) revert AlreadyAnchored(orgId, period, existing);
        roots[orgId][period] = h;
        anchoredAt[orgId][period] = block.timestamp;
        emit Anchor(orgId, period, h, block.timestamp);
    }

    /// @notice Read-only check helper for off-chain verifiers.
    function verify(uint256 orgId, string calldata period, bytes32 h) external view returns (bool) {
        return roots[orgId][period] == h;
    }
}
