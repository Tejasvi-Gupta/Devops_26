"""
Shared enums for the platform.

Kept as plain Python enums (backed by Postgres ENUM types via SQLAlchemy)
so both the DB and the application code get validation/autocomplete on
these values, instead of passing raw strings around.
"""
import enum


class CheckRunStatus(str, enum.Enum):
    """Lifecycle status of a single agent 'Check Now' execution."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class CheckResultStatus(str, enum.Enum):
    """Outcome of checking ONE requirement during a check run."""
    SATISFIED = "satisfied"   # installed and version meets requirement
    MISSING = "missing"       # tool not found at all
    OUTDATED = "outdated"     # found, but below min_version
    ERROR = "error"           # detection itself failed (e.g. permissions)


class ActionTaken(str, enum.Enum):
    """What the agent did in response to a non-satisfied requirement."""
    NONE = "none"                    # satisfied already, no action needed
    INSTALLED = "installed"          # student approved, install succeeded
    SKIPPED_BY_STUDENT = "skipped_by_student"  # student declined the prompt
    INSTALL_FAILED = "install_failed"          # attempted, but failed
