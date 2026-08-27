import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict


class StudentCreate(BaseModel):
    name: str
    email: EmailStr


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: EmailStr
    created_at: datetime
