import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.auth import require_instructor, get_current_user, CurrentUser
from app.database import get_db
from app.models import Student, Enrollment, CheckRun, EnvironmentDefinition
from app.schemas import (
    StudentStatusOut,
    StudentEnvironmentStatus,
    RequirementStatus,
    ComplianceSummary,
    StudentRisk,
    RiskReport,
)
from app.services.risk import score_student

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


def _recent_check_runs(db: Session, student_id, env_def_id, limit: int = 2) -> list[CheckRun]:
    return (
        db.query(CheckRun)
        .options(selectinload(CheckRun.results))
        .filter(
            CheckRun.student_id == student_id,
            CheckRun.environment_definition_id == env_def_id,
        )
        .order_by(CheckRun.triggered_at.desc())
        .limit(limit)
        .all()
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
def get_student_status(
    student_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    if user.role == "student" and user.id != student_id:
        raise HTTPException(status_code=403, detail="Cannot view another student's status")

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
def get_compliance_summary(
    env_def_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(require_instructor),
):
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


@router.get(
    "/environment-definitions/{env_def_id}/risk-report",
    response_model=RiskReport,
)
def get_risk_report(
    env_def_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(require_instructor),
):
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

    students = []
    for enrollment in enrollments:
        runs = _recent_check_runs(db, enrollment.student_id, env_def.id, limit=2)
        latest = runs[0] if runs else None
        previous = runs[1] if len(runs) > 1 else None
        score, level, fraction, reasons = score_student(
            latest, previous, len(env_def.requirements)
        )
        students.append(
            StudentRisk(
                student_id=enrollment.student.id,
                student_name=enrollment.student.name,
                risk_score=score,
                risk_level=level,
                unresolved_fraction=fraction,
                last_checked_at=latest.triggered_at if latest else None,
                reasons=reasons,
            )
        )

    students.sort(key=lambda s: s.risk_score, reverse=True)

    return RiskReport(
        environment_definition_id=env_def.id,
        environment_definition_name=env_def.name,
        students=students,
    )
