"""
Read-model schemas for dashboard endpoints. These aggregate data across
CheckRun/CheckResult rather than mapping 1:1 to a single table, so they
live separately from the entity schemas.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import CheckResultStatus, ActionTaken


class RequirementStatus(BaseModel):
    requirement_id: uuid.UUID
    tool_name: str
    min_version: str
    found_version: str | None = None
    status: CheckResultStatus
    action_taken: ActionTaken


class StudentEnvironmentStatus(BaseModel):
    """A student's latest check-run outcome for one environment definition."""
    environment_definition_id: uuid.UUID
    environment_definition_name: str
    last_check_run_id: uuid.UUID | None = None
    last_checked_at: datetime | None = None
    requirements: list[RequirementStatus] = []


class StudentStatusOut(BaseModel):
    student_id: uuid.UUID
    student_name: str
    environments: list[StudentEnvironmentStatus] = []


class ComplianceSummary(BaseModel):
    """Instructor-facing rollup: how many students satisfy every requirement."""
    environment_definition_id: uuid.UUID
    environment_definition_name: str
    total_enrolled: int
    fully_compliant: int
    students: list[StudentStatusOut] = []
