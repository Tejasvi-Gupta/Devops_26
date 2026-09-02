from tests.conftest import auth_header, create_env, register


def test_compliance_rollup_counts_enrolled_students(client):
    instructor = register(client, role="instructor", email="prof@uni.edu")
    alice = register(client, role="student", email="alice@uni.edu", name="Alice")
    bob = register(client, role="student", email="bob@uni.edu", name="Bob")
    env = create_env(client, instructor["access_token"])

    client.post(
        "/enrollments",
        headers=auth_header(alice["access_token"]),
        json={"environment_definition_id": env["id"]},
    )
    client.post(
        "/enrollments",
        headers=auth_header(bob["access_token"]),
        json={"environment_definition_id": env["id"]},
    )

    satisfied = [
        {
            "requirement_id": req["id"],
            "found_version": "9.9.9",
            "status": "satisfied",
            "action_taken": "none",
        }
        for req in env["requirements"]
    ]
    missing = [
        {
            "requirement_id": req["id"],
            "found_version": None,
            "status": "missing",
            "action_taken": "skipped_by_student",
        }
        for req in env["requirements"]
    ]

    client.post(
        "/check-runs",
        headers=auth_header(alice["access_token"]),
        json={
            "environment_definition_id": env["id"],
            "status": "completed",
            "results": satisfied,
        },
    )
    client.post(
        "/check-runs",
        headers=auth_header(bob["access_token"]),
        json={
            "environment_definition_id": env["id"],
            "status": "completed",
            "results": missing,
        },
    )

    summary = client.get(
        f"/environment-definitions/{env['id']}/compliance",
        headers=auth_header(instructor["access_token"]),
    )
    assert summary.status_code == 200
    body = summary.json()
    assert body["total_enrolled"] == 2
    assert body["fully_compliant"] == 1

    student_status = client.get(
        f"/students/{alice['user']['id']}/status",
        headers=auth_header(alice["access_token"]),
    )
    assert student_status.status_code == 200
    assert student_status.json()["environments"][0]["requirements"][0]["status"] == "satisfied"


def test_student_cannot_read_another_students_status(client):
    instructor = register(client, role="instructor", email="prof@uni.edu")
    alice = register(client, role="student", email="alice@uni.edu", name="Alice")
    bob = register(client, role="student", email="bob@uni.edu", name="Bob")
    env = create_env(client, instructor["access_token"])
    client.post(
        "/enrollments",
        headers=auth_header(alice["access_token"]),
        json={"environment_definition_id": env["id"]},
    )

    response = client.get(
        f"/students/{alice['user']['id']}/status",
        headers=auth_header(bob["access_token"]),
    )
    assert response.status_code == 403


def test_student_cannot_read_compliance(client):
    instructor = register(client, role="instructor", email="prof@uni.edu")
    student = register(client, role="student", email="alice@uni.edu")
    env = create_env(client, instructor["access_token"])
    response = client.get(
        f"/environment-definitions/{env['id']}/compliance",
        headers=auth_header(student["access_token"]),
    )
    assert response.status_code == 403
