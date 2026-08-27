# Frontend

React + Vite + Tailwind dashboard with two views: **Instructor** (create
environment definitions, view compliance across enrolled students) and
**Student** (enroll, view your own status against each requirement).

## What's here

- `src/api/client.js` — fetch wrapper for the backend, calls go through `/api`
- `src/components/Shell.jsx` — header + nav between Instructor/Student views
- `src/components/StatusBadge.jsx` — colored badge for satisfied/outdated/missing/error
- `src/pages/InstructorPage.jsx` — create instructor, create environment + requirements, view compliance table
- `src/pages/StudentPage.jsx` — create/select student, enroll, view status table

## Setup

```
cd frontend
npm install
```

## Run it

**1. Make sure the backend is running first** (see `backend/README.md`) —
Postgres up, migrations applied, `uvicorn app.main:app --reload` running on
port 8000.

**2. Start the frontend dev server:**
```
npm run dev
```

Open the URL it prints (typically **http://localhost:5173**).

The dev server proxies any `/api/*` request to `http://127.0.0.1:8000`
(see `vite.config.js`), so the frontend never needs to know the backend's
exact port or deal with CORS in the browser.

## What was verified

Ran both servers together and drove the UI with real seeded data (an
instructor, an environment definition with 3 requirements, and 2 students
with different compliance states). Confirmed:

- Instructor page correctly lists environment definitions and, when one is
  selected, shows a live compliance table (X / Y fully compliant) with
  accurate per-requirement status badges for each enrolled student.
- Student page correctly shows a detailed per-tool table (required vs.
  found version, status) matching exactly what was submitted via a
  check-run — including the "Missing" case (no found_version) and
  "Outdated" case (found but below minimum).
- Nav between Instructor/Student views works and highlights the active tab.

## Next steps

- Build (Phase 5): add a Dockerfile + wire into the root `docker-compose.yml`
  alongside the backend and Postgres.
- Polish: loading skeletons, toast notifications instead of inline error
  banners, form validation messages.
