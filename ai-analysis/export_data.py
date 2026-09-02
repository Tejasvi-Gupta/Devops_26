"""
Pulls check-run data out of the backend via its API and flattens it into a
single CSV: one row per (student, requirement, check_run). This is the
input the rest of the AI layer works from.

Usage:
    python export_data.py --backend-url http://127.0.0.1:8000 --out data.csv \\
        --email prof@university.edu --password <password>
"""
import argparse
import csv
import sys

import requests


def _login(backend_url: str, email: str, password: str) -> dict:
    resp = requests.post(
        f"{backend_url}/auth/login",
        json={"email": email, "password": password, "role": "instructor"},
        timeout=10,
    )
    resp.raise_for_status()
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def export_data(backend_url: str, out_path: str, email: str, password: str) -> int:
    headers = _login(backend_url, email, password)

    students = requests.get(f"{backend_url}/students", headers=headers, timeout=15).json()
    env_defs = requests.get(
        f"{backend_url}/environment-definitions", headers=headers, timeout=15
    ).json()
    env_defs_by_id = {e["id"]: e for e in env_defs}

    rows = []
    for student in students:
        check_runs = requests.get(
            f"{backend_url}/check-runs",
            params={"student_id": student["id"]},
            headers=headers,
            timeout=15,
        ).json()

        for run in check_runs:
            env_def = env_defs_by_id.get(run["environment_definition_id"])
            env_name = env_def["name"] if env_def else "unknown"

            req_by_id = {}
            if env_def:
                req_by_id = {r["id"]: r for r in env_def["requirements"]}

            for result in run["results"]:
                req = req_by_id.get(result["requirement_id"], {})
                rows.append({
                    "student_id": student["id"],
                    "student_name": student["name"],
                    "environment_definition_id": run["environment_definition_id"],
                    "environment_name": env_name,
                    "check_run_id": run["id"],
                    "triggered_at": run["triggered_at"],
                    "tool_name": req.get("tool_name", "unknown"),
                    "min_version": req.get("min_version", ""),
                    "found_version": result["found_version"] or "",
                    "status": result["status"],
                    "action_taken": result["action_taken"],
                })

    if not rows:
        print("No check-run data found. Run the Student Agent at least once first.", file=sys.stderr)
        return 1

    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"Exported {len(rows)} rows to {out_path}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Export check-run data for analysis")
    parser.add_argument("--backend-url", default="http://127.0.0.1:8000")
    parser.add_argument("--out", default="data.csv")
    parser.add_argument("--email", required=True, help="Instructor account email")
    parser.add_argument("--password", required=True, help="Instructor account password")
    args = parser.parse_args()
    sys.exit(export_data(args.backend_url, args.out, args.email, args.password))


if __name__ == "__main__":
    main()
