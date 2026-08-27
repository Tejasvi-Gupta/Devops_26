"""
Pulls check-run data out of the backend via its API and flattens it into a
single CSV: one row per (student, requirement, check_run). This is the
input the rest of the AI layer works from.

Usage:
    python export_data.py --backend-url http://127.0.0.1:8000 --out data.csv
"""
import argparse
import csv
import sys

import requests


def export_data(backend_url: str, out_path: str) -> int:
    students = requests.get(f"{backend_url}/students").json()
    env_defs = requests.get(f"{backend_url}/environment-definitions").json()
    env_defs_by_id = {e["id"]: e for e in env_defs}

    rows = []
    for student in students:
        check_runs = requests.get(
            f"{backend_url}/check-runs", params={"student_id": student["id"]}
        ).json()

        for run in check_runs:
            env_def = env_defs_by_id.get(run["environment_definition_id"])
            env_name = env_def["name"] if env_def else "unknown"

            # Map requirement_id -> requirement details for this environment,
            # so we can attach tool_name/min_version to each result row.
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
    args = parser.parse_args()
    sys.exit(export_data(args.backend_url, args.out))


if __name__ == "__main__":
    main()
