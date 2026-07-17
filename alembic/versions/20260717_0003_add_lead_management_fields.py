"""add lead management fields

Revision ID: 20260717_0003
Revises: 20260717_0002
Create Date: 2026-07-17
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260717_0003"
down_revision: str | None = "20260717_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("leads", sa.Column("notes", sa.Text(), nullable=True))
    op.add_column("leads", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f("ix_leads_deleted_at"), "leads", ["deleted_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_leads_deleted_at"), table_name="leads")
    op.drop_column("leads", "deleted_at")
    op.drop_column("leads", "notes")
