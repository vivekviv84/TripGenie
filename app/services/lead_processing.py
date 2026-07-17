import re
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from app.core.constants import DEFAULT_LEAD_STATUS
from app.core.exceptions import LeadProcessingError
from app.core.logging import get_logger
from app.models.lead import Lead
from app.repositories.lead_repository import LeadRepository
from app.schemas.webhook import IncomingWebhook, LeadProcessingResult
from app.services.lead_scoring import LeadScoringService
from app.services.lead_sync import LeadSyncService

logger = get_logger(__name__)


class LeadProcessingService:
    """Coordinate extraction, normalization, and persistence of webhook leads."""

    def __init__(
        self,
        lead_repository: LeadRepository,
        lead_scoring_service: LeadScoringService,
        lead_sync_service: LeadSyncService | None = None,
    ) -> None:
        self.lead_repository = lead_repository
        self.lead_scoring_service = lead_scoring_service
        self.lead_sync_service = lead_sync_service

    def process_call_end_webhook(self, payload: IncomingWebhook) -> LeadProcessingResult:
        """Process a validated call-end webhook and persist the lead."""

        conversation_id = self._clean_text(payload.call.conversation_id)
        logger.info("Lead processing started for conversation_id=%s", conversation_id or "missing")

        values = self._build_lead_values(payload, conversation_id)
        scoring_result = self.lead_scoring_service.score(values)
        values.update(
            {
                "lead_score": scoring_result.lead_score,
                "lead_priority": scoring_result.lead_priority,
                "lead_reason": scoring_result.lead_reason,
                "booking_intent": scoring_result.booking_intent,
                "travel_urgency": scoring_result.travel_urgency,
                "lead_summary": scoring_result.lead_summary,
                "next_action": scoring_result.next_action,
                "follow_up_action": scoring_result.follow_up_action,
            }
        )

        try:
            existing_lead = (
                self.lead_repository.get_by_conversation_id(conversation_id)
                if conversation_id
                else None
            )

            if existing_lead is None:
                lead = self.lead_repository.create(values)
                created = True
            else:
                lead = self.lead_repository.update(existing_lead, self._webhook_owned_update_values(values))
                created = False

            self.lead_repository.commit()
        except SQLAlchemyError:
            self.lead_repository.rollback()
            logger.exception("Lead persistence failed for conversation_id=%s", conversation_id or "missing")
            raise
        except Exception as exc:
            self.lead_repository.rollback()
            logger.exception("Lead processing failed for conversation_id=%s", conversation_id or "missing")
            raise LeadProcessingError("Lead could not be processed") from exc

        sheet_sync_succeeded = self._sync_lead_to_secondary_destination(lead, created)

        logger.info(
            "Lead processing completed for conversation_id=%s lead_id=%s created=%s sheet_sync_succeeded=%s",
            conversation_id or "missing",
            lead.id,
            created,
            sheet_sync_succeeded,
        )
        return LeadProcessingResult(
            lead_id=str(lead.id),
            conversation_id=lead.conversation_id,
            created=created,
            normalized_fields=values,
        )

    def _sync_lead_to_secondary_destination(self, lead: Lead, created: bool) -> bool:
        """Sync a committed lead to the secondary destination without failing the webhook."""

        if self.lead_sync_service is None:
            return False

        if created:
            return self.lead_sync_service.append_lead(lead)

        return self.lead_sync_service.update_lead(lead)

    def _build_lead_values(self, payload: IncomingWebhook, conversation_id: str | None) -> dict[str, Any]:
        """Extract and normalize ORM-ready lead values."""

        lead = payload.lead
        call = payload.call

        return {
            "customer_name": self._clean_text(lead.customer_name) or "Unknown",
            "phone": self._normalize_phone(lead.phone) or "unknown",
            "destination": self._title_case(self._clean_text(lead.destination)),
            "travel_month": self._clean_text(lead.travel_month),
            "travellers": self._to_positive_int(lead.travellers),
            "trip_type": self._clean_text(lead.trip_type),
            "budget": self._to_decimal(lead.budget),
            "hotel_preference": self._clean_text(lead.hotel_preference),
            "additional_requirements": self._clean_text(lead.additional_requirements),
            "status": DEFAULT_LEAD_STATUS,
            "call_duration": self._to_non_negative_int(call.call_duration),
            "outcome": self._clean_text(call.outcome),
            "conversation_id": conversation_id,
            "recording_url": self._clean_text(str(call.recording_url)) if call.recording_url else None,
            "raw_payload": payload.model_dump(mode="json"),
        }

    @staticmethod
    def _webhook_owned_update_values(values: dict[str, Any]) -> dict[str, Any]:
        """Return fields safe to overwrite when a duplicate webhook arrives."""

        preserved_workflow_fields = {"status"}
        return {
            field_name: field_value
            for field_name, field_value in values.items()
            if field_name not in preserved_workflow_fields
        }

    @staticmethod
    def _clean_text(value: Any) -> str | None:
        """Trim text and collapse repeated whitespace."""

        if value is None:
            return None
        cleaned = re.sub(r"\s+", " ", str(value)).strip()
        return cleaned or None

    @classmethod
    def _title_case(cls, value: str | None) -> str | None:
        """Normalize destination-style values to readable title case."""

        if value is None:
            return None
        return value.title()

    @classmethod
    def _normalize_phone(cls, value: Any) -> str | None:
        """Normalize phone text without guessing country-specific formatting."""

        cleaned = cls._clean_text(value)
        if cleaned is None:
            return None
        return re.sub(r"[^\d+]", "", cleaned)

    @classmethod
    def _to_positive_int(cls, value: Any) -> int | None:
        """Convert a value to a positive integer when possible."""

        cleaned = cls._clean_text(value)
        if cleaned is None:
            return None
        match = re.search(r"-?\d+", cleaned)
        if match is None:
            return None
        parsed = int(match.group())
        return parsed if parsed > 0 else None

    @classmethod
    def _to_non_negative_int(cls, value: Any) -> int | None:
        """Convert a value to a non-negative integer when possible."""

        cleaned = cls._clean_text(value)
        if cleaned is None:
            return None
        match = re.search(r"-?\d+", cleaned)
        if match is None:
            return None
        parsed = int(match.group())
        return parsed if parsed >= 0 else None

    @classmethod
    def _to_decimal(cls, value: Any) -> Decimal | None:
        """Convert budget-like text into a Decimal when possible."""

        cleaned = cls._clean_text(value)
        if cleaned is None:
            return None
        normalized = re.sub(r"[^\d.]", "", cleaned)
        if not normalized:
            return None
        try:
            return Decimal(normalized)
        except InvalidOperation:
            return None
