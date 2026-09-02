"""
Thin HTTP client wrapping the backend endpoints the agent actually needs:
login, fetch an environment definition, and submit a check run.
"""
import requests


class BackendClient:
    def __init__(self, base_url: str, token: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.token = token

    def _headers(self) -> dict:
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    def login(self, email: str, password: str, role: str = "student") -> str:
        resp = requests.post(
            f"{self.base_url}/auth/login",
            json={"email": email, "password": password, "role": role},
            timeout=10,
        )
        resp.raise_for_status()
        self.token = resp.json()["access_token"]
        return self.token

    def get_environment_definition(self, env_def_id: str) -> dict:
        resp = requests.get(
            f"{self.base_url}/environment-definitions/{env_def_id}",
            headers=self._headers(),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def submit_check_run(
        self,
        environment_definition_id: str,
        status: str,
        results: list[dict],
    ) -> dict:
        payload = {
            "environment_definition_id": environment_definition_id,
            "status": status,
            "results": results,
        }
        resp = requests.post(
            f"{self.base_url}/check-runs",
            json=payload,
            headers=self._headers(),
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
