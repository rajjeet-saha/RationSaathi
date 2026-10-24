from __future__ import annotations

from tests.conftest import auth, start_session


def _find(grievances, prefix):
    return next(g for g in grievances if g["id"].startswith(prefix))


def test_21_day_grievance_has_unverified_deadline_and_is_not_labelled_overdue(client):
    session = start_session(client)
    resp = client.get("/api/v1/grievances", headers=auth(session["token"]))
    assert resp.status_code == 200
    g = _find(resp.json()["grievances"], "grv-21day")
    assert g["status"] != "OVERDUE"
    assert g["deadline"]["deadline_verified"] is False
    assert g["deadline"]["deadline_at"] is None
    assert g["deadline"]["overdue"] is False
    assert "deadline not verified" in g["deadline"]["deadline_note"].lower()
    assert g["deadline"]["filed_days_ago"] == 21
    assert g["response_recorded"] is False


def test_verified_deadline_past_and_unanswered_marks_overdue(client):
    session = start_session(client)
    resp = client.get("/api/v1/grievances", headers=auth(session["token"]))
    g = _find(resp.json()["grievances"], "grv-overdue")
    assert g["deadline"]["deadline_verified"] is True
    assert g["status"] == "OVERDUE"
    assert g["deadline"]["overdue"] is True


def test_resolved_grievance_is_not_overdue(client):
    session = start_session(client)
    resp = client.get("/api/v1/grievances", headers=auth(session["token"]))
    g = _find(resp.json()["grievances"], "grv-resolved")
    assert g["status"] == "RESOLVED"
    assert g["deadline"]["overdue"] is False


def test_ownership_shows_needs_verification_when_office_unverified(client):
    session = start_session(client)
    resp = client.get("/api/v1/grievances", headers=auth(session["token"]))
    g = _find(resp.json()["grievances"], "grv-21day")
    assert g["office_verified"] is False
    assert "needs verification" in g["ownership"].lower()
    g2 = _find(resp.json()["grievances"], "grv-overdue")
    assert g2["office_verified"] is True
    assert "District Supply Office" in g2["ownership"]


def test_escalation_draft_is_privacy_preserving_and_not_submitted(client):
    session = start_session(client)
    headers = auth(session["token"])
    resp = client.post("/api/v1/grievances/grv-21day/escalation-draft", json={}, headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["state_label"] == "DRAFT — NOT SUBMITTED"
    text = body["body"]
    # No verified deadline -> must state it has not been verified, not invent one.
    assert "no verified service deadline" in text.lower()
    assert "not been verified" in text.lower() or "no verified service deadline" in text.lower()
    # Placeholder for the unverified receipt/officer, never a fabricated one.
    assert "not verified" in text.lower()
    assert body["placeholders"]["official_receipt"] == "SYN-RCPT-GRV-0021"
    # No invented law or statute.
    for banned in ["Section", "Act", "Article", "Supreme Court"]:
        assert banned not in text
    # Must ask for the responsible office to be identified.
    assert "responsible office" in text.lower()
    # No member identity leaked into the letter.
    assert "Ramesh Kumr" not in text
    assert "Ramesh Kumar" not in text


def test_escalation_letter_read_back_uses_synthetic_filing_date(client):
    session = start_session(client)
    resp = client.post(
        "/api/v1/grievances/grv-21day/escalation-draft", json={}, headers=auth(session["token"])
    ).json()
    # Filing date is present and labelled.
    assert "Filing date" in resp["body"]


def test_escalation_submission_requires_original_receipt(client):
    # grv-21day has a synthetic receipt but unverified office -> should be blocked
    # (ownership not verified) OR require confirmation. We assert it does not silently succeed.
    session = start_session(client)
    headers = auth(session["token"])
    draft = client.post("/api/v1/grievances/grv-21day/escalation-draft", json={}, headers=headers).json()
    resp = client.post(
        f"/api/v1/grievances/escalations/{draft['id']}/submit",
        json={"confirm_authorised_channel": True},
        headers=headers,
    )
    # Office is unverified, so submission must be refused.
    assert resp.status_code == 409, resp.text
    assert "office" in resp.json()["detail"].lower()


def test_escalation_submission_requires_explicit_confirmation(client):
    session = start_session(client)
    headers = auth(session["token"])
    draft = client.post("/api/v1/grievances/grv-overdue/escalation-draft", json={}, headers=headers).json()
    resp = client.post(
        f"/api/v1/grievances/escalations/{draft['id']}/submit",
        json={"confirm_authorised_channel": False},
        headers=headers,
    )
    assert resp.status_code == 400


def test_verified_office_escalation_submits_via_simulated_adapter(client):
    session = start_session(client)
    headers = auth(session["token"])
    draft = client.post("/api/v1/grievances/grv-overdue/escalation-draft", json={}, headers=headers).json()
    resp = client.post(
        f"/api/v1/grievances/escalations/{draft['id']}/submit",
        json={"confirm_authorised_channel": True},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    receipt = body["escalation"]["submitted_receipt"]
    assert receipt["is_simulated"] is True
    assert receipt["verified"] is True
    assert receipt["receipt_number"].startswith("SIM-")
    assert body["grievance"]["status"] == "ESCALATED"
    assert "not a government receipt" in body["message"].lower()


def test_escalation_draft_editable_and_persists(client):
    session = start_session(client)
    headers = auth(session["token"])
    draft = client.post("/api/v1/grievances/grv-21day/escalation-draft", json={}, headers=headers).json()
    updated = client.patch(
        f"/api/v1/grievances/escalations/{draft['id']}",
        json={"body": "Edited letter body.\n\n[Signature]"},
        headers=headers,
    )
    assert updated.status_code == 200, updated.text
    assert "Edited letter body" in updated.json()["body"]


def test_cross_household_grievance_is_hidden(client):
    a = start_session(client, household_id="hh-syn-1042", member_id="mem-a2")
    resp_a = client.get("/api/v1/grievances", headers=auth(a["token"]))
    ids_a = {g["id"] for g in resp_a.json()["grievances"]}

    b = start_session(client, household_id="hh-syn-2077", member_id="mem-b1")
    resp_b = client.get("/api/v1/grievances", headers=auth(b["token"]))
    ids_b = {g["id"] for g in resp_b.json()["grievances"]}

    assert "grv-handover-b" in ids_b
    assert "grv-handover-b" not in ids_a
    assert not ids_a & ids_b


def test_cross_household_grievance_detail_is_404(client):
    a = start_session(client, household_id="hh-syn-1042", member_id="mem-a2")
    b = start_session(client, household_id="hh-syn-2077", member_id="mem-b1")
    resp = client.get("/api/v1/grievances/grv-21day", headers=auth(b["token"]))
    assert resp.status_code == 404
