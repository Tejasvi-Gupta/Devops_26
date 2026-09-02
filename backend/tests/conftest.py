"""Shared fixtures for API tests. Requires a running Postgres (CI and local Docker)."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import SessionLocal
from app.main import app


@pytest.fixture(autouse=True)
def clean_db():
    db = SessionLocal()
    try:
        db.execute(
            text(
                "TRUNCATE TABLE check_results, check_runs, enrollments, "
                "requirements, environment_definitions, students, instructors "
                "RESTART IDENTITY CASCADE"
            )
        )
        db.commit()
    finally:
        db.close()
    yield


@pytest.fixture
def client():
    return TestClient(app)


def register(client: TestClient, *, role: str, email: str, name: str = "User"):
    response = client.post(
        "/auth/register",
        json={
            "name": name,
            "email": email,
            "password": "password123",
            "role": role,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def create_env(client: TestClient, instructor_token: str, name: str = "CS101"):
    response = client.post(
        "/environment-definitions",
        headers=auth_header(instructor_token),
        json={
            "name": name,
            "requirements": [
                {"tool_name": "python", "min_version": "3.11.0"},
                {"tool_name": "git", "min_version": "2.0.0"},
            ],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()
