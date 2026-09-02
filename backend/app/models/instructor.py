"""
Instructor: owns Environment Definitions.

password_hash is stored as a bcrypt hash; the plaintext password never
leaves the auth layer.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Instructor(Base):
    __tablename__ = "instructors"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # One instructor -> many environment definitions
    environment_definitions: Mapped[list["EnvironmentDefinition"]] = relationship(
        back_populates="created_by", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Instructor {self.email}>"
