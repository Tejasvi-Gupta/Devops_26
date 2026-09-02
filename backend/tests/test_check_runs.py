from tests.conftest import auth_header, create_env, register


def _enroll(client, student_token, env_id):
    response = client.post(
        "/enrollments",
        headers=auth_header(student_token),
        json={"environment_definition_id": env_id},
    )
    assert response.status_code == 201
    return response.json()


def _result_payload(env, status="satisfied"):
    return [
        {
            "requirement_id": req["id"],
            "found_version": "3.12.0" if req["tool_name"] == "python" else "2.40.0",
            "status": status,
            "action_taken": "none",
        }
        for req in env["requirements"]
    ]


def test_enrolled_student_can_submit_check_run(client):
    instructor = register(client, role="instructor", email="prof@uni.edu")
    student = register(client, role="student", email="alice@uni.edu", name="Alice")
    env = create_env(client, instructor["access_token"])
    _enroll(client, student["access_token"], env["id"])

    response = client.post(
        "/check-runs",
        headers=auth_header(student["access_token"]),
        json={
            "environment_definition_id": env["id"],
            "status": "completed",
            "results": _result_payload(env),
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["student_id"] == student["user"]["id"]
    assert len(body["results"]) == 2


def test_unenrolled_student_cannot_submit_check_run(client):
    instructor = register(client, role="instructor", email="prof@uni.edu")
    student = register(client, role="student", email="alice@uni.edu")
    env = create_env(client, instructor["access_token"])

    response = client.post(
        "/check-runs",
        headers=auth_header(student["access_token"]),
        json={
            "environment_definition_id": env["id"],
            "status": "completed",
            "results": _result_payload(env),
        },
    )
    assert response.status_code == 403
    assert "not enrolled" in response.json()["detail"]


def test_cannot_spoof_another_student_id(client):
    instructor = register(client, role="instructor", email="prof@uni.edu")
    alice = register(client, role="student", email="alice@uni.edu", name="Alice")
    bob = register(client, role="student", email="bob@uni.edu", name="Bob")
    env = create_env(client, instructor["access_token"])
    _enroll(client, alice["access_token"], env["id"])
    _enroll(client, bob["access_token"], env["id"])

    response = client.post(
        "/check-runs",
        headers=auth_header(alice["access_token"]),
        json={
            "student_id": bob["user"]["id"],
            "environment_definition_id": env["id"],
            "status": "completed",
            "results": _result_payload(env),
        },
    )
    assert response.status_code == 403
    assert "does not match" in response.json()["detail"]


def test_submit_without_token_is_unauthorized(client):
    response = client.post(
        "/check-runs",
        json={"environment_definition_id": "00000000-0000-0000-0000-000000000001", "results": []},
    )
    assert response.status_code == 401


def test_instructor_cannot_submit_check_run(client):
    instructor = register(client, role="instructor", email="prof@uni.edu")
    env = create_env(client, instructor["access_token"])
    response = client.post(
        "/check-runs",
        headers=auth_header(instructor["access_token"]),
        json={
            "environment_definition_id": env["id"],
            "status": "completed",
            "results": _result_payload(env),
        },
    )
    assert response.status_code == 403
