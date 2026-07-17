from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class LeadResponse(BaseModel):
    """Lead representation returned by management APIs."""

    id: UUID
    customer_name: str
    phone: str
    destination: str | None
    travel_month: str | None
    travellers: int | None
    trip_type: str | None
    budget: Decimal | None
    hotel_preference: str | None
    additional_requirements: str | None
    notes: str | None
    lead_score: int | None
    lead_priority: str
    lead_reason: str | None
    booking_intent: str | None
    travel_urgency: str | None
    status: str
    next_action: str
    follow_up_action: str | None
    lead_summary: str | None
    call_duration: int | None
    outcome: str | None
    conversation_id: str | None
    recording_url: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LeadListResponse(BaseModel):
    """Paginated lead list response."""

    items: list[LeadResponse]
    total: int
    page: int
    page_size: int
    pages: int


class LeadUpdateRequest(BaseModel):
    """Fields consultants are allowed to update manually."""

    status: str | None = Field(default=None, max_length=40)
    notes: str | None = None
    follow_up_action: str | None = Field(default=None, max_length=160)
