"""Application configuration.

Environment-driven. All values have safe demo defaults; production deployment is
expected to override DATABASE_URL, SESSION_TTL_MINUTES and ALLOW_SIMULATED_SUBMISSION.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPO_DIR / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "RationSaathi API"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"

    # Default is an on-disk SQLite file so the demo runs without any external
    # service. Set DATABASE_URL=postgresql+psycopg://... to use PostgreSQL.
    database_url: str = f"sqlite:///{(BACKEND_DIR / 'var' / 'rationsaathi.db').as_posix()}"

    demo_mode: bool = True
    allow_simulated_submission: bool = True
    session_ttl_minutes: int = 45
    facilitator_session_ttl_minutes: int = 15
    max_active_sessions_per_household: int = 25

    rules_version: str = "synthetic-2026.1"
    frontend_origin: str = "http://localhost:5173"

    # Public aggregate suppression threshold (k-anonymity).
    aggregate_min_group_size: int = 5


@lru_cache
def get_settings() -> Settings:
    return Settings()
