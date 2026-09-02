from tests.conftest import auth_header, create_env, register


def test_student_enrolls_as_themselves(client):
    instructor = register(client, role="instructor", email="prof@uni.edu", name="Prof")
    student = register(client, role="student", email="alice@uni.edu", name="Alice")
    env = create_env(client, instructor["access_token"])

    response = client.post(
        "/enrollments",
        headers=auth_header(student["access_token"]),
        json={"environment_definition_id": env["id"]},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["student_id"] == student["user"]["id"]
    assert body["environment_definition_id"] == env["id"]


def test_duplicate_enrollment_conflict(client):
    instructor = register(client, role="instructor", email="prof@uni.edu")
    student = register(client, role="student", email="alice@uni.edu")
    env = create_env(client, instructor["access_token"])
    headers = auth_header(student["access_token"])
    payload = {"environment_definition_id": env["id"]}

    assert client.post("/enrollments", headers=headers, json=payload).status_code == 201
    again = client.post("/enrollments", headers=headers, json=payload)
    assert again.status_code == 409


def test_instructor_cannot_enroll(client):
    instructor = register(client, role="instructor", email="prof@uni.edu")
    env = create_env(client, instructor["access_token"])
    response = client.post(
        "/enrollments",
        headers=auth_header(instructor["access_token"]),
        json={"environment_definition_id": env["id"]},
    )
    assert response.status_code == 403


def test_enroll_unknown_environment_404(client):
    student = register(client, role="student", email="alice@uni.edu")
    response = client.post(
        "/enrollments",
        headers=auth_header(student["access_token"]),
        json={"environment_definition_id": "00000000-0000-0000-0000-000000000001"},
    )
    assert response.status_code == 404


def test_student_lists_only_own_enrollments(client):
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

    alice_list = client.get("/enrollments", headers=auth_header(alice["access_token"]))
    assert alice_list.status_code == 200
    assert len(alice_list.json()) == 1
    assert alice_list.json()[0]["student_id"] == alice["user"]["id"]

    instructor_list = client.get(
        "/enrollments", headers=auth_header(instructor["access_token"])
    )
    assert len(instructor_list.json()) == 2
