"""
Thin HTTP client wrapping the backend endpoints the agent actually needs:
fetch an environment definition (to get its requirements), and submit a
check run once detection is done.
"""
import requests


class BackendClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def get_environment_definition(self, env_def_id: str) -> dict:
        resp = requests.get(
            f"{self.base_url}/environment-definitions/{env_def_id}", timeout=10
        )
        resp.raise_for_status()
        return resp.json()

    def submit_check_run(
        self, student_id: str, environment_definition_id: str,
        status: str, results: list[dict],
    ) -> dict:
        payload = {
            "student_id": student_id,
            "environment_definition_id": environment_definition_id,
            "status": status,
            "results": results,
        }
        resp = requests.post(f"{self.base_url}/check-runs", json=payload, timeout=15)
        resp.raise_for_status()
        return resp.json()
