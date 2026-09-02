from tests.conftest import auth_header, register


def test_health_is_public(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_register_and_login_instructor(client):
    created = register(client, role="instructor", email="prof@uni.edu", name="Prof")
    assert created["user"]["role"] == "instructor"
    assert created["access_token"]

    login = client.post(
        "/auth/login",
        json={"email": "prof@uni.edu", "password": "password123", "role": "instructor"},
    )
    assert login.status_code == 200
    me = client.get("/auth/me", headers=auth_header(login.json()["access_token"]))
    assert me.status_code == 200
    assert me.json()["email"] == "prof@uni.edu"


def test_login_rejects_wrong_password(client):
    register(client, role="student", email="alice@uni.edu", name="Alice")
    response = client.post(
        "/auth/login",
        json={"email": "alice@uni.edu", "password": "wrongpass", "role": "student"},
    )
    assert response.status_code == 401


def test_protected_route_requires_token(client):
    response = client.get("/environment-definitions")
    assert response.status_code == 401


def test_student_cannot_create_environment(client):
    student = register(client, role="student", email="alice@uni.edu", name="Alice")
    response = client.post(
        "/environment-definitions",
        headers=auth_header(student["access_token"]),
        json={"name": "CS101", "requirements": [{"tool_name": "python", "min_version": "3.11.0"}]},
    )
    assert response.status_code == 403


def test_duplicate_email_conflict(client):
    register(client, role="instructor", email="prof@uni.edu")
    again = client.post(
        "/auth/register",
        json={
            "name": "Other",
            "email": "prof@uni.edu",
            "password": "password123",
            "role": "instructor",
        },
    )
    assert again.status_code == 409
