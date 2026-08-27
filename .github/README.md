# CI/CD (Phase 7, step 1)

`.github/workflows/ci.yml` runs automatically on every push and pull
request to `main`. Four jobs run in parallel:

| Job | What it checks |
|---|---|
| `backend` | Installs deps, runs the real Alembic migration against a fresh Postgres service container, confirms the FastAPI app imports with all routes registered, runs `pytest` if a `backend/tests/` folder exists |
| `frontend` | `npm ci` + `npm run build` — catches broken imports, JSX errors, build failures |
| `student-agent` | Confirms all modules import cleanly, runs `versioning.py`'s core logic checks |
| `docker-build` | Builds both Docker images (runs only after `backend` and `frontend` pass) |

## Why a real Postgres in CI, not SQLite

Phase 6 taught us this the hard way: a real bug (the enum `.name` vs
`.value` mismatch) was invisible against SQLite and only surfaced against
real Postgres. Testing migrations against SQLite in CI would have let that
bug through a "passing" pipeline. The `backend` job spins up an actual
`postgres:16` service container and runs the real migration against it,
the same way `docker-compose.yml` does.

## Getting this running on GitHub

**1. Create a new repository on GitHub** (via github.com — "New repository").
Don't initialize it with a README/gitignore, since you already have files locally.

**2. Push your existing project to it**, from `C:\Student-env`:
```powershell
cd C:\Student-env
git init
git add .
git commit -m "Initial commit: phases 1-7 step 1"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo-name>.git
git push -u origin main
```

**3. Watch it run**: go to your repo on GitHub → the **Actions** tab. You
should see a workflow run start automatically, with the 4 jobs above
running (3 in parallel, then `docker-build` after).

## What to expect on the first run

Every step in this workflow was manually run end-to-end (migration
against real Postgres, frontend build, agent unit tests) before being
committed here, and all passed. The one thing that could NOT be verified
in advance is `docker-build`, since Docker wasn't available in the
environment these files were authored in — but both Dockerfiles were
already confirmed working via your own `docker compose up --build` run in
Phase 5, so this should also pass.

**If something fails on the first real GitHub run anyway**, that's fine —
paste the failing job's log and we'll fix it, the same way we've handled
every other phase.

## What's NOT in this workflow yet (future steps in Phase 7)

- Security scanning (SonarQube, Snyk, Trivy) — next step, plugs in as
  additional jobs/steps in this same file
- Pushing built images to a registry (e.g. Docker Hub, AWS ECR) — needed
  once we deploy somewhere real
- Actual deployment trigger — comes after Terraform/Kubernetes exist
- A `.gitignore` — you'll want one before pushing, see below

## Add a .gitignore before your first push

To avoid committing `node_modules/`, `venv/`, `.env`, and build artifacts:
