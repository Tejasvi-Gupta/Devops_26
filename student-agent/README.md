# Student Agent

A CLI that runs on a student's machine, checks their installed tools
against an instructor-defined Environment Definition, and reports the
results back to the backend.

## What's here

- `agent.py` — CLI entrypoint (`python agent.py check ...`)
- `detection.py` — detects whether a tool is installed and what version
  (built-in recipes for python, node, git, docker, npm; falls back to a
  requirement's custom `version_check_cmd` for anything else)
- `versioning.py` — dependency-free semantic version comparison
- `backend_client.py` — talks to the FastAPI backend

## Setup

```
cd student-agent
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## Usage

You need an **environment definition UUID** and a **student login**
(email + password, or a JWT from `POST /auth/login`).

**Dry run** (detect + print only, no prompts, nothing sent to the backend —
good for testing):
```
python agent.py check --env-id <uuid> --email <email> --password <password> --dry-run
```

**Real run** (prompts for missing/outdated tools, submits results):
```
python agent.py check --env-id <uuid> --email <email> --password <password>
```

By default the agent talks to `http://127.0.0.1:8000`. Override with:
```
python agent.py check --env-id <uuid> --email <email> --password <password> --backend-url http://your-backend:8000
```

## v1 scope (by design)

- **Detect + report only.** The agent does not install anything
  automatically. When a tool is missing or outdated, it shows an install
  link and asks the student to install manually, then optionally re-checks
  before submitting.
- **Manual trigger.** No background scheduling — the student runs `check`
  when they want a status update.

## What was verified

Ran end-to-end against a live backend: seeded an instructor, an
environment definition with 3 requirements (python, git, docker), a
student, and an enrollment — then ran the agent for real. It correctly
detected Python and Git as installed & satisfied, correctly reported
Docker as missing, prompted the student, recorded the decline as
`skipped_by_student`, and submitted a check run that the backend's
`/students/{id}/status` endpoint then reflected accurately.

## Extending this later

- **Auto-install**: add real install logic (e.g. `winget`, `choco`, or
  platform-specific installers) inside `_handle_missing` /
  `_handle_outdated` in `agent.py`, gated behind a `--auto-install` flag
  so the safe manual-approval flow stays the default.
- **More built-in tools**: add entries to `TOOL_CHECKS` in `detection.py`.
- **Scheduling**: wrap `run_check()` in a scheduled task (Windows Task
  Scheduler / cron) once the manual flow is trusted.
