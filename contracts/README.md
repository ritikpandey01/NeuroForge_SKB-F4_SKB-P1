# CarbonLens anchoring contract

`CarbonLensAnchor.sol` is a minimal append-only registry of Merkle roots.
The backend computes a 32-byte root over every input that feeds a report
(activity rows, factor versions, evidence files, methodology snapshot,
PDF bytes) and submits it here. Nothing about the underlying data is
stored on-chain — only the root commitment.

## Design constraints

- **Append-only.** `anchor()` reverts if `(orgId, period)` already has a
  non-zero root. Re-anchoring would let a compromised key silently
  replace a prior commitment.
- **Owner-gated writes.** Only the deployer address can anchor. Reads
  are public.
- **Chain choice: Polygon PoS.** ~USD 0.001-0.01 per anchor, 2-3s
  block time, EVM-compatible. Amoy testnet (80002) for demos; mainnet
  (137) for production.

## Deploy (Amoy testnet)

```bash
cd contracts
npm install --save-dev hardhat @nomicfoundation/hardhat-toolbox dotenv
cp .env.example .env
# edit .env: set PRIVATE_KEY (hex, no 0x prefix) to a funded Amoy account
# faucet: https://faucet.polygon.technology/ (select Amoy)

npx hardhat compile
npx hardhat run scripts/deploy.js --network amoy
```

Copy the printed contract address into `backend/.env`:

```
CHAIN_MODE=polygon-amoy
POLYGON_RPC_URL=https://rpc-amoy.polygon.technology
ANCHOR_CONTRACT_ADDRESS=0x...
ANCHOR_PRIVATE_KEY=...          # same key used to deploy
ANCHOR_CHAIN_ID=80002
ANCHOR_EXPLORER_URL=https://amoy.polygonscan.com
```

Then restart the backend and hit `POST /reports/{id}/anchor`. The
response includes a PolygonScan link.

## Demo mode (no deploy needed)

Leave `CHAIN_MODE=simulated` in the backend. The `/anchor` endpoint
returns deterministic fake tx hashes and `chain="polygon-simulated"` —
useful for walkthrough demos without funding a wallet.
