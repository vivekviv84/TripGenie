import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, Numeric, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import DEFAULT_LEAD_PRIORITY, DEFAULT_LEAD_STATUS, DEFAULT_NEXT_ACTION
from app.db.base import Base


class Lead(Base):
    """Travel lead captured from a completed Hooman voice-agent call."""

    __tablename__ = "leads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    customer_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    destination: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    travel_month: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    travellers: Mapped[int | None] = mapped_column(Integer, nullable=True)
    trip_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    budget: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    hotel_preference: Mapped[str | None] = mapped_column(String(120), nullable=True)
    additional_requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    google_sheet_row: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lead_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lead_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    booking_intent: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    travel_urgency: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    lead_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    follow_up_action: Mapped[str | None] = mapped_column(String(160), nullable=True)
    lead_priority: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        server_default=DEFAULT_LEAD_PRIORITY,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        server_default=DEFAULT_LEAD_STATUS,
        index=True,
    )
    next_action: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        server_default=DEFAULT_NEXT_ACTION,
    )
    call_duration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    outcome: Mapped[str | None] = mapped_column(String(120), nullable=True)
    conversation_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    recording_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    __table_args__ = (
        CheckConstraint("travellers IS NULL OR travellers > 0", name="ck_leads_travellers_positive"),
        CheckConstraint("lead_score IS NULL OR lead_score BETWEEN 0 AND 100", name="ck_leads_lead_score_range"),
        CheckConstraint("call_duration IS NULL OR call_duration >= 0", name="ck_leads_call_duration_non_negative"),
        Index(
            "uq_leads_conversation_id_not_null",
            "conversation_id",
            unique=True,
            postgresql_where=text("conversation_id IS NOT NULL"),
        ),
        Index("ix_leads_status_priority_created_at", "status", "lead_priority", "created_at"),
    )
