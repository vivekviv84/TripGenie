"""create leads table

Revision ID: 20260717_0001
Revises:
Create Date: 2026-07-17
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260717_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    op.create_table(
        "leads",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("customer_name", sa.String(length=120), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("destination", sa.String(length=120), nullable=True),
        sa.Column("travel_month", sa.String(length=40), nullable=True),
        sa.Column("travellers", sa.Integer(), nullable=True),
        sa.Column("trip_type", sa.String(length=80), nullable=True),
        sa.Column("budget", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("hotel_preference", sa.String(length=120), nullable=True),
        sa.Column("additional_requirements", sa.Text(), nullable=True),
        sa.Column("lead_score", sa.Integer(), nullable=True),
        sa.Column("lead_priority", sa.String(length=40), server_default="unqualified", nullable=False),
        sa.Column("status", sa.String(length=40), server_default="new", nullable=False),
        sa.Column("next_action", sa.String(length=80), server_default="review_lead", nullable=False),
        sa.Column("call_duration", sa.Integer(), nullable=True),
        sa.Column("outcome", sa.String(length=120), nullable=True),
        sa.Column("conversation_id", sa.String(length=120), nullable=True),
        sa.Column("recording_url", sa.Text(), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("call_duration IS NULL OR call_duration >= 0", name="ck_leads_call_duration_non_negative"),
        sa.CheckConstraint("lead_score IS NULL OR lead_score BETWEEN 0 AND 100", name="ck_leads_lead_score_range"),
        sa.CheckConstraint("travellers IS NULL OR travellers > 0", name="ck_leads_travellers_positive"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_leads_destination"), "leads", ["destination"], unique=False)
    op.create_index(op.f("ix_leads_lead_priority"), "leads", ["lead_priority"], unique=False)
    op.create_index(op.f("ix_leads_phone"), "leads", ["phone"], unique=False)
    op.create_index(op.f("ix_leads_status"), "leads", ["status"], unique=False)
    op.create_index("ix_leads_status_priority_created_at", "leads", ["status", "lead_priority", "created_at"], unique=False)
    op.create_index(op.f("ix_leads_travel_month"), "leads", ["travel_month"], unique=False)
    op.create_index(
        "uq_leads_conversation_id_not_null",
        "leads",
        ["conversation_id"],
        unique=True,
        postgresql_where=sa.text("conversation_id IS NOT NULL"),
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_leads_set_updated_at
        BEFORE UPDATE ON leads
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at()
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_leads_set_updated_at ON leads")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at")
    op.drop_index("uq_leads_conversation_id_not_null", table_name="leads", postgresql_where=sa.text("conversation_id IS NOT NULL"))
    op.drop_index(op.f("ix_leads_travel_month"), table_name="leads")
    op.drop_index("ix_leads_status_priority_created_at", table_name="leads")
    op.drop_index(op.f("ix_leads_status"), table_name="leads")
    op.drop_index(op.f("ix_leads_phone"), table_name="leads")
    op.drop_index(op.f("ix_leads_lead_priority"), table_name="leads")
    op.drop_index(op.f("ix_leads_destination"), table_name="leads")
    op.drop_table("leads")
