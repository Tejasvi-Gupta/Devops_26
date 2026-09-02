import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.auth import require_student, get_current_user, CurrentUser
from app.database import get_db
from app.models import CheckRun, CheckResult, Enrollment, EnvironmentDefinition
from app.schemas import CheckRunCreate, CheckRunOut

router = APIRouter(prefix="/check-runs", tags=["check-runs"])


@router.post("", response_model=CheckRunOut, status_code=201)
def submit_check_run(
    payload: CheckRunCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_student),
):
    """
    The Student Agent POSTs here after finishing a 'Check Now' pass.

    The authenticated student is the only identity recorded. A spoofed
    student_id in the body is rejected. The student must already be
    enrolled in the environment definition.
    """
    if payload.student_id is not None and payload.student_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="student_id does not match the authenticated student",
        )

    env_def = (
        db.query(EnvironmentDefinition)
        .options(selectinload(EnvironmentDefinition.requirements))
        .filter(EnvironmentDefinition.id == payload.environment_definition_id)
        .first()
    )
    if not env_def:
        raise HTTPException(status_code=404, detail="Environment definition not found")

    enrolled = (
        db.query(Enrollment)
        .filter(
            Enrollment.student_id == user.id,
            Enrollment.environment_definition_id == env_def.id,
        )
        .first()
    )
    if not enrolled:
        raise HTTPException(
            status_code=403,
            detail="Student is not enrolled in this environment definition",
        )

    valid_requirement_ids = {r.id for r in env_def.requirements}
    for result in payload.results:
        if result.requirement_id not in valid_requirement_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Requirement {result.requirement_id} does not belong to "
                       f"environment definition {env_def.id}",
            )

    check_run = CheckRun(
        student_id=user.id,
        environment_definition_id=payload.environment_definition_id,
        status=payload.status,
    )
    db.add(check_run)
    db.flush()  # get check_run.id

    for result in payload.results:
        db.add(
            CheckResult(
                check_run_id=check_run.id,
                requirement_id=result.requirement_id,
                found_version=result.found_version,
                status=result.status,
                action_taken=result.action_taken,
            )
        )

    db.commit()
    check_run = (
        db.query(CheckRun)
        .options(selectinload(CheckRun.results))
        .filter(CheckRun.id == check_run.id)
        .first()
    )
    return check_run


@router.get("/{check_run_id}", response_model=CheckRunOut)
def get_check_run(
    check_run_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    check_run = (
        db.query(CheckRun)
        .options(selectinload(CheckRun.results))
        .filter(CheckRun.id == check_run_id)
        .first()
    )
    if not check_run:
        raise HTTPException(status_code=404, detail="Check run not found")
    if user.role == "student" and check_run.student_id != user.id:
        raise HTTPException(status_code=403, detail="Cannot view another student's check run")
    return check_run


@router.get("", response_model=list[CheckRunOut])
def list_check_runs(
    student_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    query = db.query(CheckRun).options(selectinload(CheckRun.results))
    if user.role == "student":
        query = query.filter(CheckRun.student_id == user.id)
    elif student_id:
        query = query.filter(CheckRun.student_id == student_id)
    return query.order_by(CheckRun.triggered_at.desc()).all()
