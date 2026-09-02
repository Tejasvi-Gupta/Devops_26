from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
    CurrentUser,
)
from app.database import get_db
from app.models import Instructor, Student
from app.schemas.auth import AuthUserOut, LoginRequest, RegisterRequest, TokenOut

router = APIRouter(prefix="/auth", tags=["auth"])


def _token_for(user, role: str) -> TokenOut:
    return TokenOut(
        access_token=create_access_token(
            user_id=user.id, role=role, email=user.email
        ),
        user=AuthUserOut(
            id=user.id,
            name=user.name,
            email=user.email,
            role=role,
            created_at=user.created_at,
        ),
    )


@router.post("/register", response_model=TokenOut, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    password_hash = hash_password(payload.password)

    if payload.role == "instructor":
        user = Instructor(
            name=payload.name, email=payload.email, password_hash=password_hash
        )
    else:
        user = Student(
            name=payload.name, email=payload.email, password_hash=password_hash
        )

    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    db.refresh(user)
    return _token_for(user, payload.role)


@router.post("/login", response_model=TokenOut)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    model = Instructor if payload.role == "instructor" else Student
    user = db.query(model).filter(model.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    return _token_for(user, payload.role)


@router.get("/me", response_model=AuthUserOut)
def me(user: CurrentUser = Depends(get_current_user)):
    return AuthUserOut(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        created_at=user.created_at,
    )
