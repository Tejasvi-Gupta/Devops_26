"""
Student Agent CLI.

Usage:
    python agent.py check --student-id <uuid> --env-id <uuid> [--backend-url URL] [--dry-run]

What it does:
    1. Fetches the Environment Definition (and its Requirements) from the backend.
    2. For each requirement, detects whether the tool is installed and at
       what version.
    3. For anything missing/outdated, prompts the student -- v1 does not
       auto-install, it tells the student what to run and asks them to
       confirm once done (or skip).
    4. Submits the full check run + per-requirement results back to the backend.

This is v1 scope: detect + report, with student-driven action rather than
automatic installation. See README.md in this folder for how installation
gets added later without changing the report contract.
"""
import argparse
import sys

from detection import detect_tool
from versioning import meets_minimum
from backend_client import BackendClient

# Manual install pointers shown to the student when a tool is missing/outdated.
# Keyed by lowercase tool name; falls back to a generic message otherwise.
INSTALL_HINTS = {
    "python": "https://www.python.org/downloads/",
    "node": "https://nodejs.org/",
    "git": "https://git-scm.com/downloads",
    "docker": "https://www.docker.com/products/docker-desktop/",
    "npm": "npm is bundled with Node.js -- reinstalling Node usually fixes this",
}


def run_check(student_id: str, env_id: str, backend_url: str, dry_run: bool) -> int:
    client = BackendClient(backend_url)

    print(f"Fetching environment definition {env_id} ...")
    try:
        env_def = client.get_environment_definition(env_id)
    except Exception as e:
        print(f"ERROR: could not fetch environment definition: {e}", file=sys.stderr)
        return 1

    requirements = env_def.get("requirements", [])
    if not requirements:
        print("This environment definition has no requirements. Nothing to check.")
        return 0

    print(f"Environment: {env_def['name']} ({len(requirements)} requirement(s))\n")

    results = []
    for req in requirements:
        tool_name = req["tool_name"]
        min_version = req["min_version"]
        version_check_cmd = req.get("version_check_cmd")

        print(f"Checking {tool_name} (need >= {min_version}) ...", end=" ")
        detection = detect_tool(tool_name, version_check_cmd)

        if not detection.found:
            print("NOT FOUND")
            status, action_taken = _handle_missing(tool_name, dry_run)
        elif detection.version is None:
            print("FOUND, but couldn't determine version")
            status, action_taken = "error", "none"
        else:
            ok = meets_minimum(detection.version, min_version)
            if ok is True:
                print(f"OK ({detection.version})")
                status, action_taken = "satisfied", "none"
            elif ok is False:
                print(f"OUTDATED (found {detection.version})")
                status, action_taken = _handle_outdated(tool_name, detection.version, min_version, dry_run)
            else:
                print(f"FOUND ({detection.version}), but versions weren't comparable")
                status, action_taken = "error", "none"

        results.append({
            "requirement_id": req["id"],
            "found_version": detection.version,
            "status": status,
            "action_taken": action_taken,
        })

    print()
    if dry_run:
        print("[dry run] Skipping report submission. Results that would be sent:")
        for r in results:
            print(f"  {r}")
        return 0

    print("Submitting results to backend ...")
    try:
        check_run = client.submit_check_run(
            student_id=student_id,
            environment_definition_id=env_id,
            status="completed",
            results=results,
        )
    except Exception as e:
        print(f"ERROR: could not submit check run: {e}", file=sys.stderr)
        return 1

    print(f"Done. Check run id: {check_run['id']}")
    satisfied = sum(1 for r in results if r["status"] == "satisfied")
    print(f"{satisfied}/{len(results)} requirements satisfied.")
    return 0


def _handle_missing(tool_name: str, dry_run: bool) -> tuple[str, str]:
    hint = INSTALL_HINTS.get(tool_name.lower(), "(no install link available for this tool)")
    if dry_run:
        return "missing", "none"
    print(f"    '{tool_name}' is not installed. Install it from: {hint}")
    answer = input(f"    Have you installed {tool_name}? Re-check now? [y/N]: ").strip().lower()
    if answer == "y":
        recheck = detect_tool(tool_name)
        if recheck.found and recheck.version:
            print(f"    Re-checked: found {tool_name} {recheck.version}")
            return "satisfied", "installed"
        print(f"    Still not detected. Marking as skipped for this run.")
        return "missing", "skipped_by_student"
    return "missing", "skipped_by_student"


def _handle_outdated(tool_name: str, found_version: str, min_version: str, dry_run: bool) -> tuple[str, str]:
    hint = INSTALL_HINTS.get(tool_name.lower(), "(no install link available for this tool)")
    if dry_run:
        return "outdated", "none"
    print(f"    '{tool_name}' {found_version} is below the required {min_version}.")
    print(f"    Update it from: {hint}")
    answer = input(f"    Have you updated {tool_name}? Re-check now? [y/N]: ").strip().lower()
    if answer == "y":
        recheck = detect_tool(tool_name)
        if recheck.version and meets_minimum(recheck.version, min_version):
            print(f"    Re-checked: {tool_name} {recheck.version} now satisfies the requirement")
            return "satisfied", "installed"
        print(f"    Still outdated or unresolved. Marking as skipped for this run.")
        return "outdated", "skipped_by_student"
    return "outdated", "skipped_by_student"


def main():
    parser = argparse.ArgumentParser(description="Student Development Environment Agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser("check", help="Run a check against an environment definition")
    check_parser.add_argument("--student-id", required=True, help="Your student UUID")
    check_parser.add_argument("--env-id", required=True, help="Environment definition UUID")
    check_parser.add_argument(
        "--backend-url", default="http://127.0.0.1:8000",
        help="Backend base URL (default: http://127.0.0.1:8000)",
    )
    check_parser.add_argument(
        "--dry-run", action="store_true",
        help="Detect and print results without prompting for installs or submitting to the backend",
    )

    args = parser.parse_args()

    if args.command == "check":
        exit_code = run_check(args.student_id, args.env_id, args.backend_url, args.dry_run)
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
