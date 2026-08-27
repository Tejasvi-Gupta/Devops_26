# Student Environment Platform — Full Stack (Docker Compose)

Runs Postgres, the FastAPI backend, and the React frontend together with
one command. The Student Agent is **not** included here — it runs on each
student's own machine (see `student-agent/README.md`), since containerizing
it would defeat its purpose (it needs to see the real host environment).

## Prerequisites

- Docker Desktop (or Docker Engine + Compose plugin on Linux)

## Run everything

From the project root:

```
docker compose up --build
```

First run will take a few minutes (building images, downloading base
images). Subsequent runs are much faster since Docker caches layers.

This starts three services:

| Service | URL | Notes |
|---|---|---|
| `postgres` | `localhost:5432` | Database |
| `backend` | `localhost:8000` | FastAPI; runs Alembic migrations automatically on startup, then serves the API. `/docs` available. |
| `frontend` | `localhost:5173` | Nginx serving the built React app; proxies `/api/*` to the backend container internally |

Open **http://localhost:5173** once all three are up (backend has a
healthcheck, so `frontend` won't be considered ready by Compose until the
backend can actually serve requests).

## Stopping

```
docker compose down
```

Add `-v` to also wipe the Postgres data volume (fresh database next time):
```
docker compose down -v
```

## How the pieces connect

- **backend → postgres**: connects via `DATABASE_URL=postgresql://postgres:postgres@postgres:5432/student_env_platform`.
  The hostname `postgres` is Docker Compose's internal DNS name for that
  service — not `localhost`, since backend and postgres run in separate
  containers.
- **frontend → backend**: the browser talks to nginx (port 5173, mapped to
  container port 80). Nginx proxies any `/api/*` request to
  `http://backend:8000/`, stripping the `/api` prefix — so a browser call
  to `/api/instructors` reaches the backend's `/instructors` route. See
  `frontend/nginx.conf`.
- **Student Agent → backend**: runs outside Docker entirely, on the
  student's machine, and talks to the backend's published port directly
  (`--backend-url http://localhost:8000`, or wherever the backend is
  actually deployed).

## Rebuilding after code changes

```
docker compose up --build
```

`--build` forces Docker to rebuild any image whose source changed.
Without it, Compose reuses existing images even if you edited code.

## What was verified before this was handed off

- Backend Dockerfile: dependency layer caching, `alembic upgrade head`
  runs before `uvicorn` starts (via the compose `command`, not baked into
  the image, so it always targets whatever DB it's actually connected to).
- Frontend Dockerfile: multi-stage build (Vite build → nginx serve),
  confirmed the production build succeeds with the same command Docker runs.
- Frontend's API client uses relative `/api/...` paths (not a hardcoded
  backend URL), so the exact same code works against Vite's dev proxy
  *and* nginx's proxy without changes.
- nginx config's `location /api/` + `proxy_pass http://backend:8000/`
  (both trailing slashes) correctly strips the `/api` prefix before
  forwarding — verified by hand against nginx's documented proxy_pass
  rewriting behavior.

**Not yet verified**: an actual `docker compose up --build` run end-to-end,
since Docker isn't available in the environment these files were built in.
Please run it and share the output of `docker compose up --build` (or
`docker compose logs backend` / `docker compose logs frontend` if
something fails) so any real-world issues can be caught and fixed.
