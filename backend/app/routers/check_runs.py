import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import CheckRun, CheckResult, Student, EnvironmentDefinition, Requirement
from app.schemas import CheckRunCreate, CheckRunOut

router = APIRouter(prefix="/check-runs", tags=["check-runs"])


@router.post("", response_model=CheckRunOut, status_code=201)
def submit_check_run(payload: CheckRunCreate, db: Session = Depends(get_db)):
    """
    The Student Agent POSTs here after finishing a 'Check Now' pass.
    Validates that the student, environment, and every referenced
    requirement actually exist before writing anything.
    """
    if not db.get(Student, payload.student_id):
        raise HTTPException(status_code=404, detail="Student not found")

    env_def = db.get(EnvironmentDefinition, payload.environment_definition_id)
    if not env_def:
        raise HTTPException(status_code=404, detail="Environment definition not found")

    valid_requirement_ids = {r.id for r in env_def.requirements}
    for result in payload.results:
        if result.requirement_id not in valid_requirement_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Requirement {result.requirement_id} does not belong to "
                       f"environment definition {env_def.id}",
            )

    check_run = CheckRun(
        student_id=payload.student_id,
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
    db.refresh(check_run)
    return check_run


@router.get("/{check_run_id}", response_model=CheckRunOut)
def get_check_run(check_run_id: uuid.UUID, db: Session = Depends(get_db)):
    check_run = (
        db.query(CheckRun)
        .options(selectinload(CheckRun.results))
        .filter(CheckRun.id == check_run_id)
        .first()
    )
    if not check_run:
        raise HTTPException(status_code=404, detail="Check run not found")
    return check_run


@router.get("", response_model=list[CheckRunOut])
def list_check_runs(student_id: uuid.UUID | None = None, db: Session = Depends(get_db)):
    query = db.query(CheckRun).options(selectinload(CheckRun.results))
    if student_id:
        query = query.filter(CheckRun.student_id == student_id)
    return query.order_by(CheckRun.triggered_at.desc()).all()
