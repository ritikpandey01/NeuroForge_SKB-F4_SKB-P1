from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import (
    activities,
    anomalies,
    audit,
    auth,
    dashboards,
    emissions,
    facilities,
    factors,
    health,
    orgs,
    reports,
    scenarios,
    suppliers,
    uploads,
    users,
)
from app.core.config import settings
from app.db import models  # noqa: F401 — register all mapped classes on Base.metadata
from app.db.base import Base
from app.db.migrate_inplace import ensure_columns
from app.db.session import engine


def create_app() -> FastAPI:
    # Safe to run at import time — create_all is additive (never drops or alters)
    # and ensure_columns only adds missing columns. Together they let a new
    # tenant-onboarding build come up on a previously-seeded DB without requiring
    # a reseed.
    Base.metadata.create_all(engine)
    ensure_columns(engine)

    app = FastAPI(
        title="CarbonLens",
        description="Digital Intelligent Platform for ESG Performance & GHG Monitoring",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, tags=["system"])
    app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
    app.include_router(orgs.router, prefix="/api/v1", tags=["orgs"])
    app.include_router(users.router, prefix="/api/v1", tags=["users"])
    app.include_router(factors.router, prefix="/api/v1", tags=["factors"])
    app.include_router(emissions.router, prefix="/api/v1", tags=["emissions"])
    app.include_router(facilities.router, prefix="/api/v1", tags=["facilities"])
    app.include_router(activities.router, prefix="/api/v1", tags=["activities"])
    app.include_router(uploads.router, prefix="/api/v1", tags=["uploads"])
    app.include_router(suppliers.router, prefix="/api/v1", tags=["suppliers"])
    app.include_router(anomalies.router, prefix="/api/v1", tags=["anomalies"])
    app.include_router(scenarios.router, prefix="/api/v1", tags=["scenarios"])
    app.include_router(reports.router, prefix="/api/v1", tags=["reports"])
    app.include_router(dashboards.router, prefix="/api/v1", tags=["dashboards"])
    app.include_router(audit.router, prefix="/api/v1", tags=["audit"])

    return app


app = create_app()
