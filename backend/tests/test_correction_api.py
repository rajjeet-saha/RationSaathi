from __future__ import annotations

from tests.conftest import auth, start_session

FULL_EVIDENCE = ["identity_reference", "household_reference", "member_confirmation"]


def _simulate(client, headers, *, operation="UPDATE_FIELD", member_id="mem-a2", fields=None, evidence=None, **extra):
    body = {
        "operation": operation,
        "member_id": member_id,
        "fields": fields or {},
        "evidence": evidence if evidence is not None else FULL_EVIDENCE,
    }
    body.update(extra)
    return client.post("/api/v1/corrections/simulate", json=body, headers=headers)


def test_harmless_spelling_correction_is_low_risk_and_submittable(client):
    session = start_session(client)
    headers = auth(session["token"])
    resp = _simulate(client, headers, fields={"name": "Ramesh Kumar"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["risk_level"] == "LOW"
    assert body["blocked"] is False
    assert body["requires_review"] is False
    assert body["safe_to_submit"] is True
    assert body["diff"]["member_count_before"] == body["diff"]["member_count_after"]
    assert body["diff"]["entitlement_links_before"] == body["diff"]["entitlement_links_after"]


def test_harmless_age_correction_preserves_all_relationships(client):
    session = start_session(client)
    headers = auth(session["token"])
    resp = _simulate(client, headers, fields={"age": 36})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["risk_level"] == "LOW"
    assert body["safe_to_submit"] is True
    assert body["diff"]["entitlement_links_removed"] == []
    assert body["diff"]["members_removed"] == []


def test_member_deletion_is_blocked_and_preserves_original_record(client):
    session = start_session(client)
    headers = auth(session["token"])
    resp = _simulate(client, headers, operation="DELETE_MEMBER")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["risk_level"] == "BLOCKED"
    assert body["blocked"] is True
    assert body["safe_to_submit"] is False
    codes = {f["code"] for f in body["findings"]}
    assert "member_removal_blocked" in codes
    assert "entitlement_link_removal" in codes
    assert body["diff"]["members_removed"] == ["mem-a2"]
    assert len(body["diff"]["entitlement_links_removed"]) == 3

    # The original record is untouched in the database.
    member = client.get("/api/v1/members/mem-a2", headers=headers)
    assert member.status_code == 200
    assert member.json()["full_name"] == "Ramesh Kumr"


def test_replace_member_is_blocked_and_recommends_reconciliation(client):
    session = start_session(client)
    headers = auth(session["token"])
    resp = _simulate(
        client,
        headers,
        operation="REPLACE_MEMBER",
        new_member={"name": "Ramesh Kumar", "age": 36},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["blocked"] is True
    assert "reconcil" in body["recommended_action"].lower()


def test_duplicate_creation_is_high_risk_and_not_submittable(client):
    session = start_session(client)
    headers = auth(session["token"])
    resp = _simulate(
        client,
        headers,
        operation="CREATE_MEMBER",
        new_member={"name": "Ramesh Kumar", "age": 36},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["risk_level"] in ("HIGH", "REVIEW_REQUIRED", "BLOCKED")
    assert body["safe_to_submit"] is False
    codes = {f["code"] for f in body["findings"]}
    assert "possible_duplicate_member" in codes


def test_missing_member_is_rejected_as_new_applicant_attempt(client):
    session = start_session(client)
    headers = auth(session["token"])
    resp = _simulate(
        client,
        headers,
        operation="CREATE_MEMBER",
        member_id="mem-does-not-exist",
        new_member={"name": "Nobody", "age": 30},
    )
    assert resp.status_code == 404


def test_membership_removal_via_update_is_blocked(client):
    session = start_session(client)
    headers = auth(session["token"])
    resp = _simulate(client, headers, fields={"membership_status": "REMOVED"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["blocked"] is True
    codes = {f["code"] for f in body["findings"]}
    assert "membership_removal" in codes


def test_missing_evidence_requires_review(client):
    session = start_session(client)
    headers = auth(session["token"])
    resp = _simulate(client, headers, fields={"name": "Ramesh Kumar"}, evidence=[])
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["requires_review"] is True
    assert body["safe_to_submit"] is False


def test_conflicting_evidence_requires_review(client):
    session = start_session(client)
    headers = auth(session["token"])
    resp = _simulate(client, headers, fields={"age": 40})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["risk_level"] == "REVIEW_REQUIRED"
    assert body["safe_to_submit"] is False


def test_simulation_redacts_other_members(client):
    session = start_session(client)
    headers = auth(session["token"])
    resp = _simulate(client, headers, operation="DELETE_MEMBER")
    assert resp.status_code == 200
    text = resp.text
    for secret in ["Meena Kumari", "Sunita Devi", "Arjun Kumar", "Lakshmi Devi", "mem-a1", "mem-a3"]:
        assert secret not in text, f"leaked {secret}"


def test_blocked_proposal_cannot_be_saved_as_draft(client):
    session = start_session(client)
    headers = auth(session["token"])
    sim = _simulate(client, headers, operation="DELETE_MEMBER").json()
    resp = client.post(
        f"/api/v1/corrections/{sim['proposal_id']}/draft",
        json={"evidence": FULL_EVIDENCE, "note": "x"},
        headers=headers,
    )
    assert resp.status_code == 409
    assert "cannot be saved" in resp.json()["detail"].lower()


def test_blocked_proposal_submission_is_rejected(client):
    session = start_session(client)
    headers = auth(session["token"])
    sim = _simulate(client, headers, operation="DELETE_MEMBER").json()
    resp = client.post(f"/api/v1/corrections/{sim['proposal_id']}/submit", headers=headers)
    assert resp.status_code == 409
    assert "blocked" in resp.json()["detail"].lower()


def test_review_proposal_submission_is_rejected(client):
    session = start_session(client)
    headers = auth(session["token"])
    sim = _simulate(client, headers, fields={"age": 40}).json()
    resp = client.post(f"/api/v1/corrections/{sim['proposal_id']}/submit", headers=headers)
    assert resp.status_code == 409
    assert "review" in resp.json()["detail"].lower()


def test_safe_proposal_draft_then_submit_with_simulated_receipt(client):
    session = start_session(client)
    headers = auth(session["token"])
    sim = _simulate(client, headers, fields={"name": "Ramesh Kumar"}).json()

    draft = client.post(
        f"/api/v1/corrections/{sim['proposal_id']}/draft",
        json={"evidence": FULL_EVIDENCE, "note": "spelling correction"},
        headers=headers,
    )
    assert draft.status_code == 200, draft.text
    assert draft.json()["draft_ref"].startswith("RS-D-")
    assert draft.json()["state"] == "DRAFT_NOT_SUBMITTED"

    submit = client.post(f"/api/v1/corrections/{sim['proposal_id']}/submit", headers=headers)
    assert submit.status_code == 200, submit.text
    body = submit.json()
    assert body["accepted"] is True
    assert body["is_simulated"] is True
    assert body["receipt"]["is_simulated"] is True
    assert body["receipt"]["receipt_number"].startswith("SIM-")
    assert "not a government receipt" in body["message"].lower()


def test_proposal_submission_is_idempotent(client):
    session = start_session(client)
    headers = auth(session["token"])
    sim = _simulate(client, headers, fields={"name": "Ramesh Kumar"}).json()
    first = client.post(f"/api/v1/corrections/{sim['proposal_id']}/submit", headers=headers)
    assert first.status_code == 200
    second = client.post(f"/api/v1/corrections/{sim['proposal_id']}/submit", headers=headers)
    assert second.status_code == 409
    assert "already been submitted" in second.json()["detail"].lower()


def test_cross_household_proposal_is_invisible(client):
    a = start_session(client, household_id="hh-syn-1042", member_id="mem-a2")
    sim = _simulate(client, auth(a["token"]), fields={"name": "Ramesh Kumar"}).json()
    b = start_session(client, household_id="hh-syn-2077", member_id="mem-b1")
    resp = client.get(f"/api/v1/corrections/{sim['proposal_id']}", headers=auth(b["token"]))
    assert resp.status_code == 404


def test_cross_member_proposal_read_is_forbidden(client):
    a = start_session(client, member_id="mem-a2")
    sim = _simulate(client, auth(a["token"]), fields={"name": "Ramesh Kumar"}).json()
    other = start_session(client, member_id="mem-a1")
    resp = client.get(f"/api/v1/corrections/{sim['proposal_id']}", headers=auth(other["token"]))
    assert resp.status_code == 403


def test_simulation_uses_versioned_rules(client):
    session = start_session(client)
    resp = _simulate(client, auth(session["token"]), fields={"name": "Ramesh Kumar"})
    assert resp.json()["rule_version"]
    assert "synthetic" in resp.json()["rule_version"]


def test_simulation_records_audit_event_without_sensitive_values(client):
    session = start_session(client)
    headers = auth(session["token"])
    _simulate(client, headers, operation="DELETE_MEMBER")

    from app.db import get_session_factory
    from app.models import AuditEvent
    from sqlalchemy import select

    factory = get_session_factory()
    with factory() as db:
        events = db.scalars(
            select(AuditEvent).where(AuditEvent.action.in_(["correction_simulated", "correction_blocked"]))
        ).all()
    assert events, "expected audit events"
    blob = " ".join(str(e.detail) for e in events)
    assert "Ramesh Kumr" not in blob
    assert "SYN-ID-A2" not in blob
