import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

# Must match a plain dotted-numeric version like "3.10.0" or "18" -- no
# comparison operators, since those are implied by "min_version" and the
# agent's version comparison logic can't parse them.
VERSION_PATTERN = re.compile(r"^\d+(\.\d+)*$")


class RequirementCreate(BaseModel):
    tool_name: str
    min_version: str
    version_check_cmd: str | None = None

    @field_validator("min_version")
    @classmethod
    def validate_min_version(cls, v: str) -> str:
        v = v.strip()
        if not VERSION_PATTERN.match(v):
            raise ValueError(
                f"min_version must be a plain version number like '3.10.0' "
                f"(no '>=', '<=', '~', '^', etc.) -- got '{v}'"
            )
        return v


class RequirementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tool_name: str
    min_version: str
    version_check_cmd: str | None = None


class EnvironmentDefinitionCreate(BaseModel):
    name: str
    created_by_id: uuid.UUID
    requirements: list[RequirementCreate] = []


class EnvironmentDefinitionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    created_by_id: uuid.UUID
    created_at: datetime
    requirements: list[RequirementOut] = []
