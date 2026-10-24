from tests.conftest import auth, start_session


def test_health_and_demo_mode(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["demo_mode"] is True
    assert body["simulated_submission"] is True
    assert body["status"] == "ok"


def test_seeded_five_member_household_and_demo_directory(client):
    profiles = client.get("/api/v1/demo/profiles").json()["households"]
    household = next(h for h in profiles if h["id"] == "hh-syn-1042")
    assert len(household["members"]) == 5
    scenario = client.get("/api/v1/demo/scenario").json()
    assert scenario["household_a_members"] == 5
    assert "RS-D-1042" in scenario["unsubmitted_drafts"]


def test_member_session_returns_own_profile_only(client):
    session = start_session(client)
    response = client.get("/api/v1/households/current", headers=auth(session["token"]))
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["current_member"]["id"] == "mem-a2"
    serialised = response.text
    assert "Meena Kumari" not in serialised
    assert "Sunita Devi" not in serialised
    assert "SYN-ID-A1" not in serialised
