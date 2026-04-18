// Minimal Hardhat deploy script for CarbonLensAnchor.
// Usage:
//   cd contracts
//   npm install --save-dev hardhat @nomicfoundation/hardhat-toolbox dotenv
//   cp .env.example .env   # fill in AMOY_RPC_URL + PRIVATE_KEY
//   npx hardhat run scripts/deploy.js --network amoy
//
// After deployment, paste the printed address into the backend .env
// as ANCHOR_CONTRACT_ADDRESS and flip CHAIN_MODE to "polygon-amoy".

const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  console.log("Deployer:", deployer.address);
  console.log(
    "Balance:",
    hre.ethers.formatEther(await hre.ethers.provider.getBalance(deployer.address)),
    "MATIC"
  );

  const Factory = await hre.ethers.getContractFactory("CarbonLensAnchor");
  const contract = await Factory.deploy();
  await contract.waitForDeployment();

  const addr = await contract.getAddress();
  console.log("CarbonLensAnchor deployed to:", addr);
  console.log("Block:", await hre.ethers.provider.getBlockNumber());
  console.log(
    "Explorer: https://amoy.polygonscan.com/address/" + addr
  );
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
