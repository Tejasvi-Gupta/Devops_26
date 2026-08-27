"""
FastAPI application entrypoint.

Run locally with:
    uvicorn app.main:app --reload

Then open http://127.0.0.1:8000/docs for interactive API docs.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    instructors,
    students,
    environment_definitions,
    enrollments,
    check_runs,
    status,
)

app = FastAPI(
    title="Student Development Environment Provisioning Platform",
    description="API for defining, provisioning, and tracking student dev environments.",
    version="0.1.0",
)

# Permissive CORS for local development so the Vite frontend (different
# port) can call this API. Tighten this to specific origins before any
# real deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(instructors.router)
app.include_router(students.router)
app.include_router(environment_definitions.router)
app.include_router(enrollments.router)
app.include_router(check_runs.router)
app.include_router(status.router)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
