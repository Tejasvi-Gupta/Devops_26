import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Instructor
from app.schemas import InstructorCreate, InstructorOut

router = APIRouter(prefix="/instructors", tags=["instructors"])


@router.post("", response_model=InstructorOut, status_code=201)
def create_instructor(payload: InstructorCreate, db: Session = Depends(get_db)):
    instructor = Instructor(name=payload.name, email=payload.email)
    db.add(instructor)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already registered")
    db.refresh(instructor)
    return instructor


@router.get("", response_model=list[InstructorOut])
def list_instructors(db: Session = Depends(get_db)):
    return db.query(Instructor).order_by(Instructor.created_at).all()


@router.get("/{instructor_id}", response_model=InstructorOut)
def get_instructor(instructor_id: uuid.UUID, db: Session = Depends(get_db)):
    instructor = db.get(Instructor, instructor_id)
    if not instructor:
        raise HTTPException(status_code=404, detail="Instructor not found")
    return instructor
