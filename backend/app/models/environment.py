"""
EnvironmentDefinition: the manifest an instructor authors
("CS101 Fall 2026 Setup" -> requires python>=3.11, node>=18, git).

Requirement: one tool/min_version pair belonging to a definition.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EnvironmentDefinition(Base):
    __tablename__ = "environment_definitions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("instructors.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    created_by: Mapped["Instructor"] = relationship(
        back_populates="environment_definitions"
    )
    requirements: Mapped[list["Requirement"]] = relationship(
        back_populates="environment_definition", cascade="all, delete-orphan"
    )
    enrollments: Mapped[list["Enrollment"]] = relationship(
        back_populates="environment_definition", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<EnvironmentDefinition {self.name}>"


class Requirement(Base):
    __tablename__ = "requirements"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    environment_definition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("environment_definitions.id"),
        nullable=False,
    )
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    min_version: Mapped[str] = mapped_column(String(50), nullable=False)

    # Optional override; if null, the agent uses its own built-in check
    # for well-known tools (python, node, git, docker, ...).
    version_check_cmd: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )

    environment_definition: Mapped["EnvironmentDefinition"] = relationship(
        back_populates="requirements"
    )
    check_results: Mapped[list["CheckResult"]] = relationship(
        back_populates="requirement"
    )

    def __repr__(self) -> str:
        return f"<Requirement {self.tool_name}>={self.min_version}>"
