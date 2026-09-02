import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.auth import require_instructor, get_current_user, CurrentUser
from app.database import get_db
from app.models import EnvironmentDefinition, Requirement
from app.schemas import EnvironmentDefinitionCreate, EnvironmentDefinitionOut

router = APIRouter(prefix="/environment-definitions", tags=["environment-definitions"])


@router.post("", response_model=EnvironmentDefinitionOut, status_code=201)
def create_environment_definition(
    payload: EnvironmentDefinitionCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_instructor),
):
    env_def = EnvironmentDefinition(
        name=payload.name, created_by_id=user.id
    )
    db.add(env_def)
    db.flush()  # get env_def.id without committing yet

    for req in payload.requirements:
        db.add(
            Requirement(
                environment_definition_id=env_def.id,
                tool_name=req.tool_name,
                min_version=req.min_version,
                version_check_cmd=req.version_check_cmd,
            )
        )

    db.commit()
    env_def = (
        db.query(EnvironmentDefinition)
        .options(selectinload(EnvironmentDefinition.requirements))
        .filter(EnvironmentDefinition.id == env_def.id)
        .first()
    )
    return env_def


@router.get("", response_model=list[EnvironmentDefinitionOut])
def list_environment_definitions(
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
):
    return (
        db.query(EnvironmentDefinition)
        .options(selectinload(EnvironmentDefinition.requirements))
        .order_by(EnvironmentDefinition.created_at)
        .all()
    )


@router.get("/{env_def_id}", response_model=EnvironmentDefinitionOut)
def get_environment_definition(
    env_def_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
):
    env_def = (
        db.query(EnvironmentDefinition)
        .options(selectinload(EnvironmentDefinition.requirements))
        .filter(EnvironmentDefinition.id == env_def_id)
        .first()
    )
    if not env_def:
        raise HTTPException(status_code=404, detail="Environment definition not found")
    return env_def
