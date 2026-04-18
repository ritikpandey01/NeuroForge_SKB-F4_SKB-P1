from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = "sqlite:///./data/carbonlens.db"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_MAX_TOKENS: int = 4000
    OPENAI_CB_FAILURES: int = 3
    OPENAI_CB_COOLDOWN_SECONDS: int = 60
    DOC_MAX_PAGES: int = 5
    DOC_RENDER_DPI: int = 144
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    PDF_OUTPUT_DIR: str = "./data/reports"
    LOG_LEVEL: str = "INFO"
    JWT_SECRET: str = "dev-secret-change-me-in-prod"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TTL_MINUTES: int = 60
    JWT_REFRESH_TTL_DAYS: int = 7
    # Polygon anchoring (Phase 2). When CHAIN_MODE="simulated", no RPC is
    # called — deterministic fake tx hashes + block numbers are generated
    # so the demo works without a funded wallet. Flip to "polygon" and
    # populate the RPC/contract/key fields to submit real txs.
    CHAIN_MODE: str = "simulated"  # simulated | polygon-amoy | polygon
    POLYGON_RPC_URL: str = ""
    ANCHOR_CONTRACT_ADDRESS: str = ""
    ANCHOR_PRIVATE_KEY: str = ""
    ANCHOR_CHAIN_ID: int = 80002  # Amoy testnet; mainnet is 137
    ANCHOR_EXPLORER_URL: str = "https://amoy.polygonscan.com"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def pdf_output_path(self) -> Path:
        return Path(self.PDF_OUTPUT_DIR)


settings = Settings()
