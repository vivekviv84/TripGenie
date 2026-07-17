import re
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class WebhookMetadata(BaseModel):
    """Provider metadata attached to the webhook event."""

    event_type: str | None = Field(default=None, max_length=80)
    provider: str | None = Field(default=None, max_length=80)
    sent_at: str | None = Field(default=None, max_length=80)

    model_config = ConfigDict(extra="allow")


class WebhookCallInfo(BaseModel):
    """Call-level information sent by the voice-agent platform."""

    conversation_id: str | None = Field(default=None, max_length=120)
    recording_url: HttpUrl | str | None = None
    call_duration: int | str | None = None
    outcome: str | None = Field(default=None, max_length=120)

    model_config = ConfigDict(extra="allow")


class WebhookLeadInfo(BaseModel):
    """Lead details collected during the call."""

    customer_name: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=32)
    destination: str | None = Field(default=None, max_length=120)
    travel_month: str | None = Field(default=None, max_length=40)
    travellers: int | str | None = None
    trip_type: str | None = Field(default=None, max_length=80)
    budget: Decimal | int | float | str | None = None
    hotel_preference: str | None = Field(default=None, max_length=120)
    additional_requirements: str | None = None

    model_config = ConfigDict(extra="allow")

    @field_validator("travellers")
    @classmethod
    def validate_travellers(cls, value: int | str | None) -> int | str | None:
        """Reject clearly invalid traveller counts while allowing normalization later."""

        if isinstance(value, int) and value <= 0:
            raise ValueError("travellers must be greater than zero")
        if isinstance(value, str):
            match = re.search(r"-?\d+", value.strip())
            if match is not None and int(match.group()) <= 0:
                raise ValueError("travellers must be greater than zero")
        return value


class IncomingWebhook(BaseModel):
    """Top-level Hooman call-end webhook payload."""

    metadata: WebhookMetadata | None = None
    call: WebhookCallInfo = Field(default_factory=WebhookCallInfo)
    lead: WebhookLeadInfo = Field(default_factory=WebhookLeadInfo)

    model_config = ConfigDict(extra="allow")


class WebhookProcessingResponse(BaseModel):
    """HTTP response returned after a webhook is processed."""

    status: str
    lead_id: str
    conversation_id: str | None
    created: bool
    message: str


class LeadProcessingResult(BaseModel):
    """Service-layer result used by the API response."""

    lead_id: str
    conversation_id: str | None
    created: bool
    normalized_fields: dict[str, Any]
