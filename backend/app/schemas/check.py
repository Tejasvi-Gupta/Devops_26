"""
This is the JSON contract the Student Agent uses to report a "Check Now"
run back to the backend. Keep this shape stable once the agent is built,
since changing it means changing both sides at once.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import CheckRunStatus, CheckResultStatus, ActionTaken


class CheckResultCreate(BaseModel):
    requirement_id: uuid.UUID
    found_version: str | None = None
    status: CheckResultStatus
    action_taken: ActionTaken = ActionTaken.NONE


class CheckResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    requirement_id: uuid.UUID
    found_version: str | None = None
    status: CheckResultStatus
    action_taken: ActionTaken


class CheckRunCreate(BaseModel):
    """
    Submitted by the Student Agent after it finishes a full check.
    Example payload:

    {
      "environment_definition_id": "...",
      "status": "completed",
      "results": [
        {
          "requirement_id": "...",
          "found_version": "3.10.4",
          "status": "outdated",
          "action_taken": "installed"
        }
      ]
    }

    student_id, if sent, must match the authenticated student. The
    backend always records the token's user id, never a spoofed UUID.
    """
    student_id: uuid.UUID | None = None
    environment_definition_id: uuid.UUID
    status: CheckRunStatus = CheckRunStatus.COMPLETED
    results: list[CheckResultCreate] = []


class CheckRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    student_id: uuid.UUID
    environment_definition_id: uuid.UUID
    triggered_at: datetime
    status: CheckRunStatus
    results: list[CheckResultOut] = []
