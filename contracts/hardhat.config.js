require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

const { AMOY_RPC_URL, POLYGON_RPC_URL, PRIVATE_KEY } = process.env;

module.exports = {
  solidity: {
    version: "0.8.20",
    settings: { optimizer: { enabled: true, runs: 200 } },
  },
  networks: {
    amoy: {
      url: AMOY_RPC_URL || "https://rpc-amoy.polygon.technology",
      chainId: 80002,
      accounts: PRIVATE_KEY ? [PRIVATE_KEY] : [],
    },
    polygon: {
      url: POLYGON_RPC_URL || "https://polygon-rpc.com",
      chainId: 137,
      accounts: PRIVATE_KEY ? [PRIVATE_KEY] : [],
    },
  },
};
