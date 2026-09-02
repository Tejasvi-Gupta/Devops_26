"""
FastAPI application entrypoint.

Run locally with:
    uvicorn app.main:app --reload

Then open http://127.0.0.1:8000/docs for interactive API docs.
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    auth,
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
    version="0.2.0",
)

_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
)
allow_origins = [o.strip() for o in _origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(instructors.router)
app.include_router(students.router)
app.include_router(environment_definitions.router)
app.include_router(enrollments.router)
app.include_router(check_runs.router)
app.include_router(status.router)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
