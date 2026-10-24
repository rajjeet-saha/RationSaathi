from __future__ import annotations

from tests.conftest import auth, start_session


def _draft(session_token: str, member_id: str = "mem-a2", **overrides) -> dict:
    body = {
        "kind": "CORRECTION",
        "member_id": member_id,
        "payload": {"label": "DRAFT — NOT SUBMITTED", "note": "test"},
        "idempotency_key": None,
    }
    body.update(overrides)
    return body


def test_new_draft_starts_not_submitted_and_carries_local_reference(client):
    session = start_session(client)
    headers = auth(session["token"])
    resp = client.post("/api/v1/drafts", json=_draft(session["token"]), headers=headers)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["state"] == "DRAFT_NOT_SUBMITTED"
    assert body["state_label"] == "Saved on this device — not submitted"
    assert body["draft_ref"].startswith("RS-D-")
    assert body["is_official_submission"] is False
    assert "not submitted" in body["notice"].lower()


def test_seeded_draft_is_marked_not_submitted(client):
    session = start_session(client)
    resp = client.get("/api/v1/drafts", headers=auth(session["token"]))
    assert resp.status_code == 200
    drafts = resp.json()["drafts"]
    assert drafts, "expected at least the seeded draft"
    seeded = next(d for d in drafts if d["draft_ref"] == "RS-D-1042")
    assert seeded["state"] == "DRAFT_NOT_SUBMITTED"
    assert seeded["payload"].get("label") == "DRAFT — NOT SUBMITTED"


def test_offline_sync_queues_without_claiming_submission(client):
    session = start_session(client)
    headers = auth(session["token"])
    created = client.post("/api/v1/drafts", json=_draft(session["token"]), headers=headers).json()

    resp = client.post(
        f"/api/v1/drafts/{created['id']}/sync", json={"network_online": False}, headers=headers
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["state"] == "QUEUED_FOR_SYNC"
    assert body["synced"] is False
    assert body["official_submission_confirmed"] is False
    assert "waiting for a connection" in body["message"].lower()


def test_online_sync_reaches_pending_verification_but_not_confirmed(client):
    session = start_session(client)
    headers = auth(session["token"])
    created = client.post("/api/v1/drafts", json=_draft(session["token"]), headers=headers).json()

    resp = client.post(f"/api/v1/drafts/{created['id']}/sync", json={"network_online": True}, headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["state"] == "SUBMISSION_PENDING_VERIFICATION"
    assert body["is_official_submission"] is False
    assert body["official_submission_confirmed"] is False
    assert "not confirmed" in body["message"].lower()


def test_verify_without_receipt_keeps_draft_unconfirmed(client):
    session = start_session(client)
    headers = auth(session["token"])
    created = client.post("/api/v1/drafts", json=_draft(session["token"]), headers=headers).json()
    client.post(f"/api/v1/drafts/{created['id']}/sync", json={"network_online": True}, headers=headers)

    resp = client.post(
        f"/api/v1/drafts/{created['id']}/verify-submission", json={"simulate_receipt": False}, headers=headers
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["verified"] is False
    assert body["receipt"] is None
    assert body["state"] == "SUBMISSION_PENDING_VERIFICATION"


def test_verified_submission_is_labelled_simulated(client):
    session = start_session(client)
    headers = auth(session["token"])
    created = client.post("/api/v1/drafts", json=_draft(session["token"]), headers=headers).json()
    client.post(f"/api/v1/drafts/{created['id']}/sync", json={"network_online": True}, headers=headers)

    resp = client.post(
        f"/api/v1/drafts/{created['id']}/verify-submission", json={"simulate_receipt": True}, headers=headers
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["verified"] is True
    assert body["state"] == "SUBMITTED_CONFIRMED"
    assert body["is_official_submission"] is True
    assert body["receipt"]["is_simulated"] is True
    assert body["receipt"]["receipt_number"].startswith("SIM-")
    assert "not an official government receipt" in body["message"].lower()


def test_duplicate_verification_returns_same_receipt(client):
    session = start_session(client)
    headers = auth(session["token"])
    created = client.post("/api/v1/drafts", json=_draft(session["token"]), headers=headers).json()
    client.post(f"/api/v1/drafts/{created['id']}/sync", json={"network_online": True}, headers=headers)

    first = client.post(
        f"/api/v1/drafts/{created['id']}/verify-submission", json={"simulate_receipt": True}, headers=headers
    ).json()
    second = client.post(
        f"/api/v1/drafts/{created['id']}/verify-submission", json={"simulate_receipt": True}, headers=headers
    ).json()
    assert second["receipt"]["receipt_number"] == first["receipt"]["receipt_number"]
    assert second["verified"] is True


def test_sync_after_confirmed_does_not_duplicate_submission(client):
    session = start_session(client)
    headers = auth(session["token"])
    created = client.post("/api/v1/drafts", json=_draft(session["token"]), headers=headers).json()
    client.post(f"/api/v1/drafts/{created['id']}/sync", json={"network_online": True}, headers=headers)
    client.post(f"/api/v1/drafts/{created['id']}/verify-submission", json={"simulate_receipt": True}, headers=headers)

    resp = client.post(f"/api/v1/drafts/{created['id']}/sync", json={"network_online": True}, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["official_submission_confirmed"] is True
    assert "no duplicate submission" in body["message"].lower()


def test_confirmed_draft_cannot_be_deleted(client):
    session = start_session(client)
    headers = auth(session["token"])
    created = client.post("/api/v1/drafts", json=_draft(session["token"]), headers=headers).json()
    client.post(f"/api/v1/drafts/{created['id']}/sync", json={"network_online": True}, headers=headers)
    client.post(f"/api/v1/drafts/{created['id']}/verify-submission", json={"simulate_receipt": True}, headers=headers)

    resp = client.delete(f"/api/v1/drafts/{created['id']}", headers=headers)
    assert resp.status_code == 409


def test_deleting_draft_clears_payload_but_keeps_audit_reference(client):
    session = start_session(client)
    headers = auth(session["token"])
    created = client.post("/api/v1/drafts", json=_draft(session["token"]), headers=headers).json()

    resp = client.delete(f"/api/v1/drafts/{created['id']}", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["state"] == "CANCELLED"
    assert body["payload"] == {"cleared": True, "label": "DRAFT — CANCELLED", "previous_kind": "CORRECTION"}


def test_conflicting_version_edit_is_rejected(client):
    session = start_session(client)
    headers = auth(session["token"])
    created = client.post("/api/v1/drafts", json=_draft(session["token"]), headers=headers).json()

    resp = client.patch(
        f"/api/v1/drafts/{created['id']}",
        json={"payload": {"note": "v2"}, "expected_version": 99},
        headers=headers,
    )
    assert resp.status_code == 409
    assert "updated elsewhere" in resp.json()["detail"].lower()


def test_conflicting_version_bump(client):
    session = start_session(client)
    headers = auth(session["token"])
    created = client.post("/api/v1/drafts", json=_draft(session["token"]), headers=headers).json()

    ok = client.patch(
        f"/api/v1/drafts/{created['id']}",
        json={"payload": {"note": "v2"}, "expected_version": created["version"]},
        headers=headers,
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["version"] == created["version"] + 1


def test_cross_member_draft_is_hidden(client):
    # Session as mem-a1 cannot see mem-a2's draft.
    a1 = start_session(client, member_id="mem-a1")
    resp = client.get("/api/v1/drafts", headers=auth(a1["token"]))
    assert resp.status_code == 200
    assert all(d["draft_ref"] != "RS-D-1042" or d.get("member_id") == "mem-a1" for d in resp.json()["drafts"])
    assert all(d["member_id"] == "mem-a1" for d in resp.json()["drafts"])


def test_cross_member_draft_edit_is_forbidden(client):
    a2 = start_session(client, member_id="mem-a2")
    created = client.post(
        "/api/v1/drafts", json=_draft(a2["token"], member_id="mem-a2"), headers=auth(a2["token"])
    ).json()
    a1 = start_session(client, member_id="mem-a1")
    resp = client.patch(
        f"/api/v1/drafts/{created['id']}",
        json={"payload": {}, "expected_version": created["version"]},
        headers=auth(a1["token"]),
    )
    assert resp.status_code in (403, 404)


def test_invalid_transition_is_rejected(client):
    session = start_session(client)
    headers = auth(session["token"])
    created = client.post("/api/v1/drafts", json=_draft(session["token"]), headers=headers).json()

    # Verify-submission on a brand-new draft has no pending submission to verify.
    resp = client.post(
        f"/api/v1/drafts/{created['id']}/verify-submission", json={"simulate_receipt": True}, headers=headers
    )
    assert resp.status_code == 409
