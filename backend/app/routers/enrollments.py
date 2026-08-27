from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Enrollment, Student, EnvironmentDefinition
from app.schemas import EnrollmentCreate, EnrollmentOut

router = APIRouter(prefix="/enrollments", tags=["enrollments"])


@router.post("", response_model=EnrollmentOut, status_code=201)
def create_enrollment(payload: EnrollmentCreate, db: Session = Depends(get_db)):
    if not db.get(Student, payload.student_id):
        raise HTTPException(status_code=404, detail="Student not found")
    if not db.get(EnvironmentDefinition, payload.environment_definition_id):
        raise HTTPException(status_code=404, detail="Environment definition not found")

    enrollment = Enrollment(
        student_id=payload.student_id,
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
def list_enrollments(db: Session = Depends(get_db)):
    return db.query(Enrollment).order_by(Enrollment.enrolled_at).all()
