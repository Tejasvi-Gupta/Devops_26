import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import Student, Enrollment, CheckRun, EnvironmentDefinition
from app.schemas import (
    StudentStatusOut,
    StudentEnvironmentStatus,
    RequirementStatus,
    ComplianceSummary,
)

router = APIRouter(tags=["status"])


def _latest_check_run(db: Session, student_id, env_def_id) -> CheckRun | None:
    return (
        db.query(CheckRun)
        .options(selectinload(CheckRun.results))
        .filter(
            CheckRun.student_id == student_id,
            CheckRun.environment_definition_id == env_def_id,
        )
        .order_by(CheckRun.triggered_at.desc())
        .first()
    )


def _build_student_environment_status(
    db: Session, student_id, env_def: EnvironmentDefinition
) -> StudentEnvironmentStatus:
    latest_run = _latest_check_run(db, student_id, env_def.id)

    results_by_requirement = {}
    if latest_run:
        results_by_requirement = {r.requirement_id: r for r in latest_run.results}

    requirement_statuses = []
    for req in env_def.requirements:
        result = results_by_requirement.get(req.id)
        if result:
            requirement_statuses.append(
                RequirementStatus(
                    requirement_id=req.id,
                    tool_name=req.tool_name,
                    min_version=req.min_version,
                    found_version=result.found_version,
                    status=result.status,
                    action_taken=result.action_taken,
                )
            )
        else:
            # No check run yet, or this requirement was added after the
            # last check -> report as missing so it's visible on the dashboard.
            requirement_statuses.append(
                RequirementStatus(
                    requirement_id=req.id,
                    tool_name=req.tool_name,
                    min_version=req.min_version,
                    found_version=None,
                    status="missing",
                    action_taken="none",
                )
            )

    return StudentEnvironmentStatus(
        environment_definition_id=env_def.id,
        environment_definition_name=env_def.name,
        last_check_run_id=latest_run.id if latest_run else None,
        last_checked_at=latest_run.triggered_at if latest_run else None,
        requirements=requirement_statuses,
    )


@router.get("/students/{student_id}/status", response_model=StudentStatusOut)
def get_student_status(student_id: uuid.UUID, db: Session = Depends(get_db)):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    enrollments = (
        db.query(Enrollment)
        .options(
            selectinload(Enrollment.environment_definition).selectinload(
                EnvironmentDefinition.requirements
            )
        )
        .filter(Enrollment.student_id == student_id)
        .all()
    )

    environments = [
        _build_student_environment_status(db, student.id, e.environment_definition)
        for e in enrollments
    ]

    return StudentStatusOut(
        student_id=student.id, student_name=student.name, environments=environments
    )


@router.get(
    "/environment-definitions/{env_def_id}/compliance",
    response_model=ComplianceSummary,
)
def get_compliance_summary(env_def_id: uuid.UUID, db: Session = Depends(get_db)):
    env_def = (
        db.query(EnvironmentDefinition)
        .options(selectinload(EnvironmentDefinition.requirements))
        .filter(EnvironmentDefinition.id == env_def_id)
        .first()
    )
    if not env_def:
        raise HTTPException(status_code=404, detail="Environment definition not found")

    enrollments = (
        db.query(Enrollment)
        .options(selectinload(Enrollment.student))
        .filter(Enrollment.environment_definition_id == env_def_id)
        .all()
    )

    students_status = []
    fully_compliant = 0
    for enrollment in enrollments:
        env_status = _build_student_environment_status(
            db, enrollment.student_id, env_def
        )
        is_compliant = all(r.status == "satisfied" for r in env_status.requirements)
        if is_compliant and env_status.requirements:
            fully_compliant += 1

        students_status.append(
            StudentStatusOut(
                student_id=enrollment.student.id,
                student_name=enrollment.student.name,
                environments=[env_status],
            )
        )

    return ComplianceSummary(
        environment_definition_id=env_def.id,
        environment_definition_name=env_def.name,
        total_enrolled=len(enrollments),
        fully_compliant=fully_compliant,
        students=students_status,
    )
