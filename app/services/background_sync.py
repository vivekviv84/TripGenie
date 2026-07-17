from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from typing import Any
from uuid import UUID

from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.repositories.lead_repository import LeadRepository
from app.services.lead_sync import LeadSyncService

logger = get_logger(__name__)


class BackgroundLeadSyncService:
    """Run secondary lead sync outside the webhook response path."""

    def __init__(self, lead_sync_service: LeadSyncService, max_workers: int = 2) -> None:
        self.lead_sync_service = lead_sync_service
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="lead-sync")

    def append_lead(self, lead: Any) -> bool:
        """Schedule append sync and return immediately."""

        self.executor.submit(self._run_sync, "append", self._snapshot(lead))
        return True

    def update_lead(self, lead: Any) -> bool:
        """Schedule update sync and return immediately."""

        self.executor.submit(self._run_sync, "update", self._snapshot(lead))
        return True

    def _run_sync(self, operation: str, lead_snapshot: SimpleNamespace) -> None:
        """Run one sync job and persist row tracking when available."""

        logger.info("Background lead sync started operation=%s lead_id=%s", operation, lead_snapshot.id)
        if operation == "append":
            succeeded = self.lead_sync_service.append_lead(lead_snapshot)
        else:
            succeeded = self.lead_sync_service.update_lead(lead_snapshot)

        if succeeded and getattr(lead_snapshot, "google_sheet_row", None):
            self._persist_google_sheet_row(lead_snapshot.id, lead_snapshot.google_sheet_row)
        logger.info(
            "Background lead sync completed operation=%s lead_id=%s succeeded=%s",
            operation,
            lead_snapshot.id,
            succeeded,
        )

    @staticmethod
    def _persist_google_sheet_row(lead_id: UUID, row_number: int) -> None:
        """Persist the Google Sheet row number using an independent session."""

        db = SessionLocal()
        try:
            repository = LeadRepository(db)
            repository.update_google_sheet_row(lead_id, row_number)
            repository.commit()
        except Exception:
            db.rollback()
            logger.exception("Failed to persist Google Sheet row lead_id=%s", lead_id)
        finally:
            db.close()

    @staticmethod
    def _snapshot(lead: Any) -> SimpleNamespace:
        """Copy ORM attributes needed by the Sheets mapper before the request session closes."""

        fields = (
            "id",
            "created_at",
            "customer_name",
            "phone",
            "destination",
            "travel_month",
            "travellers",
            "trip_type",
            "budget",
            "hotel_preference",
            "additional_requirements",
            "lead_score",
            "lead_priority",
            "lead_reason",
            "booking_intent",
            "travel_urgency",
            "status",
            "next_action",
            "follow_up_action",
            "lead_summary",
            "call_duration",
            "outcome",
            "conversation_id",
            "recording_url",
            "google_sheet_row",
        )
        return SimpleNamespace(**{field: getattr(lead, field, None) for field in fields})
