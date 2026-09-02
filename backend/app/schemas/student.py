import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict, Field


class StudentCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=8)


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: EmailStr
    created_at: datetime
