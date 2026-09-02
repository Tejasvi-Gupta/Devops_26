from types import SimpleNamespace

from app.models.enums import ActionTaken, CheckResultStatus
from app.services.risk import score_student
from tests.conftest import auth_header, create_env, register


def test_never_checked_student_is_high_risk(client):
    instructor = register(client, role="instructor", email="prof@uni.edu")
    student = register(client, role="student", email="alice@uni.edu", name="Alice")
    env = create_env(client, instructor["access_token"])
    client.post(
        "/enrollments",
        headers=auth_header(student["access_token"]),
        json={"environment_definition_id": env["id"]},
    )

    report = client.get(
        f"/environment-definitions/{env['id']}/risk-report",
        headers=auth_header(instructor["access_token"]),
    )
    assert report.status_code == 200
    body = report.json()
    assert len(body["students"]) == 1
    assert body["students"][0]["risk_level"] == "high"
    assert body["students"][0]["risk_score"] == 1.0
    assert "Never submitted a check run" in body["students"][0]["reasons"]


def test_compliant_student_is_low_risk(client):
    instructor = register(client, role="instructor", email="prof@uni.edu")
    student = register(client, role="student", email="alice@uni.edu", name="Alice")
    env = create_env(client, instructor["access_token"])
    client.post(
        "/enrollments",
        headers=auth_header(student["access_token"]),
        json={"environment_definition_id": env["id"]},
    )
    client.post(
        "/check-runs",
        headers=auth_header(student["access_token"]),
        json={
            "environment_definition_id": env["id"],
            "status": "completed",
            "results": [
                {
                    "requirement_id": req["id"],
                    "found_version": "9.9.9",
                    "status": "satisfied",
                    "action_taken": "none",
                }
                for req in env["requirements"]
            ],
        },
    )

    report = client.get(
        f"/environment-definitions/{env['id']}/risk-report",
        headers=auth_header(instructor["access_token"]),
    )
    assert report.status_code == 200
    row = report.json()["students"][0]
    assert row["risk_level"] == "low"
    assert row["risk_score"] == 0.0


def test_student_cannot_read_risk_report(client):
    instructor = register(client, role="instructor", email="prof@uni.edu")
    student = register(client, role="student", email="alice@uni.edu")
    env = create_env(client, instructor["access_token"])
    response = client.get(
        f"/environment-definitions/{env['id']}/risk-report",
        headers=auth_header(student["access_token"]),
    )
    assert response.status_code == 403


def _run(results):
    return SimpleNamespace(results=results)


def _result(status, action="none"):
    return SimpleNamespace(
        status=CheckResultStatus(status),
        action_taken=ActionTaken(action),
    )


def test_score_student_never_checked():
    score, level, fraction, reasons = score_student(None, None, 2)
    assert score == 1.0
    assert level == "high"
    assert fraction is None
    assert "Never submitted a check run" in reasons


def test_score_student_improving_reduces_risk():
    previous = _run([_result("missing"), _result("missing")])
    latest = _run([_result("satisfied"), _result("missing")])
    score, level, fraction, reasons = score_student(latest, previous, 2)
    assert fraction == 0.5
    assert "Improved since previous check" in reasons
    assert score < 0.5
