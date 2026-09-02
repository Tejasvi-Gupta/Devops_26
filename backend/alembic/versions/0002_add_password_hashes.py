"""add password hashes for instructors and students

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-01
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

# Sentinel stored for pre-auth rows so the column can be NOT NULL.
# verify_password() rejects any hash that starts with "!".
_UNUSABLE = "!"


def upgrade() -> None:
    op.add_column(
        "instructors",
        sa.Column("password_hash", sa.String(255), nullable=True),
    )
    op.add_column(
        "students",
        sa.Column("password_hash", sa.String(255), nullable=True),
    )
    op.execute(
        sa.text(f"UPDATE instructors SET password_hash = '{_UNUSABLE}' WHERE password_hash IS NULL")
    )
    op.execute(
        sa.text(f"UPDATE students SET password_hash = '{_UNUSABLE}' WHERE password_hash IS NULL")
    )
    op.alter_column("instructors", "password_hash", nullable=False)
    op.alter_column("students", "password_hash", nullable=False)


def downgrade() -> None:
    op.drop_column("students", "password_hash")
    op.drop_column("instructors", "password_hash")
