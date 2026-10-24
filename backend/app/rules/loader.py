"""Loads versioned rule payloads from the database with a bundled fallback."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.models import RuleVersion

RULES_DIR = Path(__file__).resolve().parent


@lru_cache
def _bundled(name: str) -> dict[str, Any]:
    return json.loads((RULES_DIR / name).read_text(encoding="utf-8"))


def load_rule_payload(db: DbSession, scope: str) -> dict[str, Any]:
    record = db.scalar(
        select(RuleVersion).where(RuleVersion.scope == scope).order_by(RuleVersion.effective_from.desc()).limit(1)
    )
    if record is None:
        return _bundled("portability_rules.json")
    payload = dict(record.payload or {})
    payload.setdefault("version", record.version)
    payload.setdefault("source_label", record.source_label)
    payload.setdefault("is_synthetic", record.is_synthetic)
    if scope == "portability":
        payload.setdefault("effective_from", record.effective_from.isoformat())
    return payload
