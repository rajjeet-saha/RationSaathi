from tests.conftest import auth, start_session


def test_member_can_read_own_profile_and_entitlements(client):
    session = start_session(client)
    headers = auth(session["token"])
    response = client.get("/api/v1/members/mem-a2", headers=headers)
    assert response.status_code == 200
    assert response.json()["full_name"] == "Ramesh Kumr"
    entitlements = client.get("/api/v1/members/mem-a2/entitlements", headers=headers)
    assert entitlements.status_code == 200
    assert {e["commodity_code"] for e in entitlements.json()["entitlements"]} >= {"RICE", "WHEAT"}


def test_cross_member_reads_are_rejected(client):
    session = start_session(client)
    headers = auth(session["token"])
    for member_id in ["mem-a1", "mem-a3", "mem-a4", "mem-a5", "mem-b1"]:
        assert client.get(f"/api/v1/members/{member_id}", headers=headers).status_code == 403
        assert client.get(f"/api/v1/members/{member_id}/entitlements", headers=headers).status_code == 403


def test_household_payload_contains_no_other_member_details(client):
    session = start_session(client)
    response = client.get("/api/v1/households/current", headers=auth(session["token"]))
    assert response.status_code == 200
    body = response.text
    for secret in ["Sunita Devi", "Meena Kumari", "Arjun Kumar", "Lakshmi Devi", "SYN-ID-A1", "mem-a1", "mem-a5"]:
        assert secret not in body, f"leaked {secret}"


def test_profile_switch_revokes_previous_token(client):
    first = start_session(client)
    old_headers = auth(first["token"])
    assert client.get("/api/v1/members/mem-a2", headers=old_headers).status_code == 200

    switched = client.post("/api/v1/sessions/switch", json={"member_id": "mem-a1"}, headers=old_headers)
    assert switched.status_code == 200, switched.text
    new_token = switched.json()["token"]
    assert new_token != first["token"]

    assert client.get("/api/v1/households/current", headers=old_headers).status_code == 401
    new_household = client.get("/api/v1/households/current", headers=auth(new_token))
    assert new_household.status_code == 200
    assert new_household.json()["current_member"]["id"] == "mem-a1"
    assert "Ramesh Kumr" not in new_household.text


def test_session_end_revokes_token_and_confirms_server_cleanup(client):
    session = start_session(client)
    headers = auth(session["token"])
    response = client.post(
        "/api/v1/sessions/end",
        json={"reason": "USER_LOGOUT", "client_cleanup_confirmed": True},
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["server_cleanup_verified"] is True
    assert body["ended"] is True
    assert any("revoked" in action for action in body["server_actions"])
    assert body["limitations"]
    assert client.get("/api/v1/households/current", headers=headers).status_code == 401


def test_facilitator_requires_consent_before_any_profile_opens(client):
    facilitator = start_session(client, member_id=None, role="FACILITATOR")
    headers = auth(facilitator["token"])
    assert client.get("/api/v1/households/current", headers=headers).status_code == 409
    assert client.get("/api/v1/members/mem-a1", headers=headers).status_code == 403

    missing = client.post(
        "/api/v1/sessions/consent",
        json={"member_id": "mem-a1", "consent_explained": False, "consent_given": False},
        headers=headers,
    )
    assert missing.status_code == 400

    granted = client.post(
        "/api/v1/sessions/consent",
        json={"member_id": "mem-a1", "consent_explained": True, "consent_given": True},
        headers=headers,
    )
    assert granted.status_code == 200, granted.text

    own = client.get("/api/v1/members/mem-a1", headers=headers)
    assert own.status_code == 200
    assert own.json()["id"] == "mem-a1"
    assert client.get("/api/v1/members/mem-a2", headers=headers).status_code == 403
    assert client.get("/api/v1/members/mem-b1", headers=headers).status_code == 403
    assert client.get("/api/v1/households/current", headers=headers).status_code == 200


def test_facilitator_cannot_switch_profile_without_a_new_session(client):
    facilitator = start_session(client, member_id=None, role="FACILITATOR")
    headers = auth(facilitator["token"])
    client.post(
        "/api/v1/sessions/consent",
        json={"member_id": "mem-a1", "consent_explained": True, "consent_given": True},
        headers=headers,
    )
    response = client.post("/api/v1/sessions/switch", json={"member_id": "mem-a2"}, headers=headers)
    assert response.status_code == 409


def test_facilitator_cannot_consent_for_another_household(client):
    facilitator = start_session(client, member_id=None, role="FACILITATOR")
    response = client.post(
        "/api/v1/sessions/consent",
        json={"member_id": "mem-b1", "consent_explained": True, "consent_given": True},
        headers=auth(facilitator["token"]),
    )
    # 404 rather than 403: the API never discloses whether a member of another
    # household exists to this session.
    assert response.status_code == 404


def test_unauthorised_correction_simulation_is_rejected(client):
    session = start_session(client)
    response = client.post(
        "/api/v1/corrections/simulate",
        json={"operation": "UPDATE_FIELD", "member_id": "mem-a1", "fields": {"name": "Changed"}, "evidence": []},
        headers=auth(session["token"]),
    )
    assert response.status_code == 403
    assert "Sunita" not in response.text


def test_facilitator_can_simulate_but_edit_is_blocked_and_redacted(client):
    facilitator = start_session(client, member_id=None, role="FACILITATOR")
    headers = auth(facilitator["token"])
    client.post(
        "/api/v1/sessions/consent",
        json={"member_id": "mem-a2", "consent_explained": True, "consent_given": True},
        headers=headers,
    )
    response = client.post(
        "/api/v1/corrections/simulate",
        json={
            "operation": "UPDATE_FIELD",
            "member_id": "mem-a2",
            "fields": {"name": "Ramesh Kumar"},
            "evidence": ["identity_reference", "household_reference", "member_confirmation"],
        },
        headers=headers,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["blocked"] is True
    assert any(f["code"] == "facilitator_cannot_edit_identity" for f in body["findings"])
    assert "Sunita Devi" not in response.text
    assert "Meena Kumari" not in response.text


def test_all_sensitive_endpoints_require_a_session(client):
    for path in ["/api/v1/households/current", "/api/v1/members/mem-a2", "/api/v1/drafts", "/api/v1/grievances"]:
        assert client.get(path).status_code == 401
    assert client.get("/api/v1/public/aggregates").status_code == 200
