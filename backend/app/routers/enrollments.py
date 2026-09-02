from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import require_student, get_current_user, CurrentUser
from app.database import get_db
from app.models import Enrollment, EnvironmentDefinition
from app.schemas import EnrollmentCreate, EnrollmentOut

router = APIRouter(prefix="/enrollments", tags=["enrollments"])


@router.post("", response_model=EnrollmentOut, status_code=201)
def create_enrollment(
    payload: EnrollmentCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_student),
):
    if not db.get(EnvironmentDefinition, payload.environment_definition_id):
        raise HTTPException(status_code=404, detail="Environment definition not found")

    enrollment = Enrollment(
        student_id=user.id,
        environment_definition_id=payload.environment_definition_id,
    )
    db.add(enrollment)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Student is already enrolled in this environment definition",
        )
    db.refresh(enrollment)
    return enrollment


@router.get("", response_model=list[EnrollmentOut])
def list_enrollments(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    query = db.query(Enrollment).order_by(Enrollment.enrolled_at)
    if user.role == "student":
        query = query.filter(Enrollment.student_id == user.id)
    return query.all()
