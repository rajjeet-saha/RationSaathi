"""RationSaathi FastAPI application."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import func, select

from app.api.v1 import corrections, demo, drafts, grievances, households, portability, public, sessions
from app.config import get_settings
from app.db import get_session_factory, utcnow
from app.models import Household

logger = logging.getLogger("rationsaathi")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.db import create_all

    create_all()
    settings = get_settings()
    factory = get_session_factory()
    if settings.demo_mode:
        with factory() as db:
            count = db.scalar(select(func.count()).select_from(Household)) or 0
        if count == 0:
            from scripts.seed import seed_all

            with factory() as db:
                summary = seed_all(db)
                db.commit()
            logger.info("Auto-seeded synthetic demo data: %s", summary)
    logger.info("RationSaathi API ready (demo_mode=%s)", settings.demo_mode)
    yield


app = FastAPI(
    title="RationSaathi API",
    version="0.1.0",
    description=(
        "Synthetic civic-tech prototype for public-distribution navigation. "
        "No government integration is connected. All seeded data is fictional."
    ),
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Ration-Session", "Authorization"],
)

app.include_router(sessions.router, prefix="/api/v1")
app.include_router(households.router, prefix="/api/v1")
app.include_router(portability.router, prefix="/api/v1")
app.include_router(corrections.router, prefix="/api/v1")
app.include_router(drafts.router, prefix="/api/v1")
app.include_router(grievances.router, prefix="/api/v1")
app.include_router(public.router, prefix="/api/v1")
app.include_router(demo.router, prefix="/api/v1")


@app.get("/api/v1/health", tags=["meta"])
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "demo_mode": settings.demo_mode,
        "rules_version": settings.rules_version,
        "database": settings.database_url.split("://", 1)[0],
        "simulated_submission": settings.allow_simulated_submission,
        "generated_at": utcnow().isoformat(),
        "is_synthetic": True,
    }


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred. No sensitive values have been logged in the response.",
        },
    )
