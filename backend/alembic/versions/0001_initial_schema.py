"""initial schema

Creates the 7 core tables: instructors, environment_definitions,
requirements, students, enrollments, check_runs, check_results.

Revision ID: 0001
Revises:
Create Date: 2026-08-23
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "instructors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "students",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "environment_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("instructors.id"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "requirements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "environment_definition_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("environment_definitions.id"),
            nullable=False,
        ),
        sa.Column("tool_name", sa.String(100), nullable=False),
        sa.Column("min_version", sa.String(50), nullable=False),
        sa.Column("version_check_cmd", sa.String(255), nullable=True),
    )

    op.create_table(
        "enrollments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("students.id"),
            nullable=False,
        ),
        sa.Column(
            "environment_definition_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("environment_definitions.id"),
            nullable=False,
        ),
        sa.Column("enrolled_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "student_id", "environment_definition_id", name="uq_student_env_def"
        ),
    )

    # create_type=False: we create these enum types explicitly below via
    # .create(checkfirst=True). Without this flag, SQLAlchemy ALSO tries to
    # auto-create the type the first time it's used as a column type in
    # create_table(), causing a "type already exists" DuplicateObject error.
    # create_type=False: prevents SQLAlchemy from auto-creating the enum
    # the first time it's used as a column type in create_table() below
    # (that auto-create has no checkfirst guard and errors if the type
    # already exists). We create the types explicitly and safely instead.
    check_run_status = postgresql.ENUM(
        "pending", "completed", "failed",
        name="check_run_status", create_type=False,
    )
    check_result_status = postgresql.ENUM(
        "satisfied", "missing", "outdated", "error",
        name="check_result_status", create_type=False,
    )
    action_taken = postgresql.ENUM(
        "none", "installed", "skipped_by_student", "install_failed",
        name="action_taken", create_type=False,
    )

    check_run_status.create(op.get_bind(), checkfirst=True)
    check_result_status.create(op.get_bind(), checkfirst=True)
    action_taken.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "check_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("students.id"),
            nullable=False,
        ),
        sa.Column(
            "environment_definition_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("environment_definitions.id"),
            nullable=False,
        ),
        sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            check_run_status,
            nullable=False,
            server_default="pending",
        ),
    )

    op.create_table(
        "check_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "check_run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("check_runs.id"),
            nullable=False,
        ),
        sa.Column(
            "requirement_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("requirements.id"),
            nullable=False,
        ),
        sa.Column("found_version", sa.String(50), nullable=True),
        sa.Column("status", check_result_status, nullable=False),
        sa.Column(
            "action_taken",
            action_taken,
            nullable=False,
            server_default="none",
        ),
    )


def downgrade() -> None:
    op.drop_table("check_results")
    op.drop_table("check_runs")
    op.drop_table("enrollments")
    op.drop_table("requirements")
    op.drop_table("environment_definitions")
    op.drop_table("students")
    op.drop_table("instructors")

    postgresql.ENUM(name="action_taken").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="check_result_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="check_run_status").drop(op.get_bind(), checkfirst=True)
