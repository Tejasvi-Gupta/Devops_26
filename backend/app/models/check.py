"""
CheckRun: one "Check Now" execution by the Student Agent.
CheckResult: the per-requirement outcome within that run.

Together these are the append-only history the whole platform is built
on — compliance dashboards, the future AI layer, and monitoring all read
from this data rather than from "current state" fields, so nothing is
ever overwritten or lost.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, Enum as SqlEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import CheckRunStatus, CheckResultStatus, ActionTaken


class CheckRun(Base):
    __tablename__ = "check_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=False
    )
    environment_definition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("environment_definitions.id"),
        nullable=False,
    )
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    status: Mapped[CheckRunStatus] = mapped_column(
        SqlEnum(
            CheckRunStatus, name="check_run_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=CheckRunStatus.PENDING,
        nullable=False,
    )

    student: Mapped["Student"] = relationship(back_populates="check_runs")
    environment_definition: Mapped["EnvironmentDefinition"] = relationship()
    results: Mapped[list["CheckResult"]] = relationship(
        back_populates="check_run", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<CheckRun {self.id} student={self.student_id} status={self.status}>"


class CheckResult(Base):
    __tablename__ = "check_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    check_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("check_runs.id"), nullable=False
    )
    requirement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("requirements.id"), nullable=False
    )
    found_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[CheckResultStatus] = mapped_column(
        SqlEnum(
            CheckResultStatus, name="check_result_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    action_taken: Mapped[ActionTaken] = mapped_column(
        SqlEnum(
            ActionTaken, name="action_taken",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=ActionTaken.NONE,
        nullable=False,
    )

    check_run: Mapped["CheckRun"] = relationship(back_populates="results")
    requirement: Mapped["Requirement"] = relationship(back_populates="check_results")

    def __repr__(self) -> str:
        return f"<CheckResult req={self.requirement_id} status={self.status}>"
