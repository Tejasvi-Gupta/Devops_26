"""
Pydantic schemas for Instructor.

Naming convention used throughout app/schemas/:
- *Create  -> what the client sends to create a new record (no id, no server-set fields)
- *Out     -> what the API returns (includes id, timestamps, nested data)
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict


class InstructorCreate(BaseModel):
    name: str
    email: EmailStr


class InstructorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # allows .model_validate(orm_obj)

    id: uuid.UUID
    name: str
    email: EmailStr
    created_at: datetime
