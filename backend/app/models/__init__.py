"""
Import every model here so SQLAlchemy's mapper configuration can resolve
all the string-based relationship() references (e.g. "EnvironmentDefinition")
regardless of which module gets imported first.
"""
from app.models.instructor import Instructor
from app.models.environment import EnvironmentDefinition, Requirement
from app.models.student import Student, Enrollment
from app.models.check import CheckRun, CheckResult
from app.models.enums import CheckRunStatus, CheckResultStatus, ActionTaken

__all__ = [
    "Instructor",
    "EnvironmentDefinition",
    "Requirement",
    "Student",
    "Enrollment",
    "CheckRun",
    "CheckResult",
    "CheckRunStatus",
    "CheckResultStatus",
    "ActionTaken",
]
