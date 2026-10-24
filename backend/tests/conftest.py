from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND = Path(__file__).resolve().parent.parent
TEST_DB = BACKEND / "var" / "test_rationsaathi.db"
TEST_DB.parent.mkdir(exist_ok=True)
if TEST_DB.exists():
    TEST_DB.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB.as_posix()}"
os.environ["DEMO_MODE"] = "true"
os.environ["ALLOW_SIMULATED_SUBMISSION"] = "true"
os.environ["SESSION_TTL_MINUTES"] = "45"
os.environ["AGGREGATE_MIN_GROUP_SIZE"] = "5"

from app.db import Base, get_engine, get_session_factory  # noqa: E402
from app.main import app  # noqa: E402
from app.security.ratelimit import reset_rate_limits  # noqa: E402
from scripts.seed import seed_all  # noqa: E402


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=get_engine())
    Base.metadata.create_all(bind=get_engine())
    factory = get_session_factory()
    with factory() as db:
        seed_all(db)
        db.commit()
    reset_rate_limits()
    with TestClient(app) as test_client:
        yield test_client


def start_session(
    client: TestClient,
    *,
    household_id: str = "hh-syn-1042",
    member_id: str | None = "mem-a2",
    role: str = "MEMBER",
) -> dict:
    response = client.post(
        "/api/v1/sessions",
        json={
            "household_id": household_id,
            "role": role,
            "member_id": member_id if role == "MEMBER" else None,
            "purpose": "ASSISTED_SERVICE" if role == "FACILITATOR" else "MEMBER_SELF_SERVICE",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def auth(token: str) -> dict[str, str]:
    return {"X-Ration-Session": token}
