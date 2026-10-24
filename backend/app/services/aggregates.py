"""Privacy-preserving public aggregates.

Only de-identified counts and distributions leave this module.

Disclosure control, in two layers:

1. Primary suppression: any cell whose group is smaller than the configured
   minimum group size is replaced with null.
2. Secondary suppression: a cell (or a partition total) is also suppressed when
   publishing it would let a reader reconstruct a suppressed cell by subtraction
   — either from a published total, or from the remainder of a partition such as
   the category breakdown. This closes the obvious differencing attack.

No names, addresses, household references, member IDs, receipt numbers or
narratives are included, and only de-identified aggregates leave this module.
"""

from __future__ import annotations

from collections import Counter
from datetime import timedelta
from statistics import median
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.config import get_settings
from app.db import ensure_aware, utcnow
from app.domain import GrievanceStatus, StockState
from app.models import Grievance, ServiceLevelPolicy, StockObservation
from app.services.grievance_service import effective_status


def _suppressed(reason: str) -> dict[str, Any]:
    return {"value": None, "suppressed": True, "reason": reason}


def _primary_cell(value: int | float, min_group: int) -> dict[str, Any]:
    if value < min_group:
        return _suppressed(f"Fewer than {min_group} records; suppressed to protect privacy.")
    return {"value": value, "suppressed": False}


def _partition(
    total: int,
    counts: dict[str, int],
    min_group: int,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any], int, bool]:
    """Suppress small cells, and suppress the total when the residual would leak.

    Returns ``(cells, total_cell, suppressed_residual, total_visible)``.
    ``suppressed_residual`` is the combined size of the cells that were hidden.
    """
    cells: dict[str, dict[str, Any]] = {}
    suppressed_residual = 0
    for key, count in sorted(counts.items()):
        if count < min_group:
            suppressed_residual += count
            cells[key] = _suppressed(f"Fewer than {min_group} records; suppressed to protect privacy.")
        else:
            cells[key] = {"value": count, "suppressed": False}

    # Publishing the total is safe only when the hidden remainder is either zero
    # or itself large enough to be non-identifying.
    if suppressed_residual == 0 or suppressed_residual >= min_group:
        total_visible = True
        total_cell: dict[str, Any] = {"value": total, "suppressed": False}
    else:
        total_visible = False
        total_cell = _suppressed(
            "Total suppressed to prevent reconstruction of a hidden cell by subtraction."
        )
    return cells, total_cell, suppressed_residual, total_visible


def _secondary_cell(count: int, total: int, total_visible: bool, min_group: int) -> dict[str, Any]:
    """A count that is safe alone but would leak a hidden complement."""
    if count < min_group:
        return _primary_cell(count, min_group)
    if total_visible:
        complement = total - count
        if 0 < complement < min_group:
            return _suppressed("Suppressed to prevent differencing against the published total.")
    return {"value": count, "suppressed": False}


def public_aggregates(db: DbSession) -> dict[str, Any]:
    settings = get_settings()
    min_group = settings.aggregate_min_group_size
    now = utcnow()

    grievances = db.scalars(select(Grievance)).all()
    total_grievances = len(grievances)

    # --- grievance category partition -----------------------------------
    categories = dict(Counter(g.category for g in grievances))
    category_cells, total_cell, _category_residual, total_visible = _partition(
        total_grievances, categories, min_group
    )

    resolved = sum(1 for g in grievances if g.status == GrievanceStatus.RESOLVED)
    overdue = 0
    for grievance in grievances:
        status, _ = effective_status(db, grievance, now)
        if status == GrievanceStatus.OVERDUE:
            overdue += 1
    awaiting = sum(
        1 for g in grievances if g.status == GrievanceStatus.FILED and not g.assigned_officer
    )

    resolved_cell = _secondary_cell(resolved, total_grievances, total_visible, min_group)
    overdue_cell = _secondary_cell(overdue, total_grievances, total_visible, min_group)
    awaiting_cell = _secondary_cell(awaiting, total_grievances, total_visible, min_group)

    # --- processing-time median ------------------------------------------
    processing_days = []
    for grievance in grievances:
        if grievance.status == GrievanceStatus.RESOLVED and grievance.filed_at and grievance.last_status_update:
            delta = ensure_aware(grievance.last_status_update) - ensure_aware(grievance.filed_at)
            processing_days.append(max(delta.total_seconds() / 86400, 0))
    sample = len(processing_days)
    if sample < min_group:
        median_cell = {
            "sample_size": None,
            "value": None,
            "suppressed": True,
            "reason": f"Fewer than {min_group} resolved cases; median and sample size suppressed.",
        }
    else:
        median_cell = {
            "sample_size": sample,
            "value": round(median(processing_days), 1),
            "suppressed": False,
            "reason": None,
        }

    # --- stock observations partition ------------------------------------
    observations = db.scalars(select(StockObservation)).all()
    total_obs = len(observations)
    state_counts = dict(Counter(o.state for o in observations))
    stock_cells, stock_total_cell, _stock_residual, stock_total_visible = _partition(
        total_obs, state_counts, min_group
    )
    fresh_cutoff = now - timedelta(hours=24)
    fresh = sum(1 for o in observations if ensure_aware(o.observed_at) >= fresh_cutoff)
    fresh_cell = _secondary_cell(fresh, total_obs, stock_total_visible, min_group)

    return {
        "generated_at": now.isoformat(),
        "window_label": "All seeded synthetic records (rolling demo window)",
        "is_synthetic": True,
        "disclaimer": (
            "Synthetic demonstration aggregates. No live government data is represented and individual households, "
            "members, receipts or shops cannot be derived from this payload."
        ),
        "minimum_group_size": min_group,
        "method": {
            "suppression": (
                f"Primary suppression: any group smaller than {min_group} records is replaced with an empty value."
            ),
            "differencing": (
                "Secondary suppression: a total, or a derived count, is hidden whenever publishing it would "
                "reconstruct a hidden cell by subtraction — including partition remainders."
            ),
            "identifiers": (
                "No names, addresses, member IDs, receipt numbers, household references, shop identities or "
                "narratives are included."
            ),
        },
        "grievances": {
            "total": total_cell,
            "by_category": [
                {"category": category, "count": cell} for category, cell in category_cells.items()
            ],
            "resolved": resolved_cell,
            "verified_overdue": overdue_cell,
            "awaiting_assignment": awaiting_cell,
            "median_processing_days": median_cell,
        },
        "stock": {
            "observations": stock_total_cell,
            "by_state": [
                {"state": state, "count": cell, "label": state} for state, cell in stock_cells.items()
            ],
            "fresh_within_24h": fresh_cell,
            "note": (
                "Counts combine verified shop records and household reports; the two are not distinguished in this "
                "aggregate view to avoid identification of individual shops. Detailed signals require an authorised "
                "reviewer."
            ),
            "all_states": [s.value for s in StockState],
        },
        "service_completion": {
            "resolved_cases": resolved_cell,
            "median_days_note": (
                "Median processing time is shown only when at least "
                f"{min_group} resolved cases are present. It is a synthetic sample statistic, not a service guarantee."
            ),
        },
        "sla_policies": [
            {
                "category": policy.category,
                "jurisdiction": policy.jurisdiction_code,
                "days": policy.days,
                "version": policy.version,
                "verified": policy.verified,
                "is_synthetic": policy.is_synthetic,
                "source_label": policy.source_label,
            }
            for policy in db.scalars(select(ServiceLevelPolicy)).all()
        ],
        "small_group_suppressed": (
            any(cell["suppressed"] for cell in category_cells.values())
            or any(cell["suppressed"] for cell in stock_cells.values())
            or not total_visible
            or not stock_total_visible
        ),
    }
