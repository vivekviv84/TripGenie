"""add lead scoring fields

Revision ID: 20260717_0002
Revises: 20260717_0001
Create Date: 2026-07-17
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260717_0002"
down_revision: str | None = "20260717_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("leads", sa.Column("lead_reason", sa.Text(), nullable=True))
    op.add_column("leads", sa.Column("booking_intent", sa.String(length=40), nullable=True))
    op.add_column("leads", sa.Column("travel_urgency", sa.String(length=40), nullable=True))
    op.add_column("leads", sa.Column("lead_summary", sa.Text(), nullable=True))
    op.add_column("leads", sa.Column("follow_up_action", sa.String(length=160), nullable=True))
    op.create_index(op.f("ix_leads_booking_intent"), "leads", ["booking_intent"], unique=False)
    op.create_index(op.f("ix_leads_travel_urgency"), "leads", ["travel_urgency"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_leads_travel_urgency"), table_name="leads")
    op.drop_index(op.f("ix_leads_booking_intent"), table_name="leads")
    op.drop_column("leads", "follow_up_action")
    op.drop_column("leads", "lead_summary")
    op.drop_column("leads", "travel_urgency")
    op.drop_column("leads", "booking_intent")
    op.drop_column("leads", "lead_reason")
