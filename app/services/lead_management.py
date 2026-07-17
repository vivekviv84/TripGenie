from math import ceil
from uuid import UUID

from fastapi import status

from app.core.exceptions import ApplicationError
from app.core.logging import get_logger
from app.repositories.lead_repository import LeadRepository
from app.schemas.lead import LeadListResponse, LeadResponse, LeadUpdateRequest

logger = get_logger(__name__)


class LeadManagementService:
    """Manage consultant-facing lead reads and updates."""

    def __init__(self, lead_repository: LeadRepository) -> None:
        self.lead_repository = lead_repository

    def list_leads(
        self,
        *,
        page: int,
        page_size: int,
        status_filter: str | None,
        priority: str | None,
        destination: str | None,
        search: str | None,
        sort_by: str,
        sort_order: str,
    ) -> LeadListResponse:
        """Return paginated, filtered, sorted leads."""

        leads, total = self.lead_repository.list_active(
            page=page,
            page_size=page_size,
            status=status_filter,
            priority=priority,
            destination=destination,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        return LeadListResponse(
            items=[LeadResponse.model_validate(lead) for lead in leads],
            total=total,
            page=page,
            page_size=page_size,
            pages=ceil(total / page_size) if total else 0,
        )

    def get_lead(self, lead_id: UUID) -> LeadResponse:
        """Return one active lead."""

        lead = self.lead_repository.get_active_by_id(lead_id)
        if lead is None:
            raise ApplicationError("Lead not found", status.HTTP_404_NOT_FOUND)
        return LeadResponse.model_validate(lead)

    def update_lead(self, lead_id: UUID, request: LeadUpdateRequest) -> LeadResponse:
        """Update consultant-editable lead fields."""

        lead = self.lead_repository.get_active_by_id(lead_id)
        if lead is None:
            raise ApplicationError("Lead not found", status.HTTP_404_NOT_FOUND)

        values = request.model_dump(exclude_unset=True)
        if values.get("follow_up_action") is not None:
            values["next_action"] = values["follow_up_action"]

        updated = self.lead_repository.update(lead, values)
        self.lead_repository.commit()
        logger.info("Lead updated lead_id=%s fields=%s", lead_id, ",".join(values.keys()))
        return LeadResponse.model_validate(updated)

    def delete_lead(self, lead_id: UUID) -> None:
        """Soft delete one lead."""

        lead = self.lead_repository.get_active_by_id(lead_id)
        if lead is None:
            raise ApplicationError("Lead not found", status.HTTP_404_NOT_FOUND)

        self.lead_repository.soft_delete(lead)
        self.lead_repository.commit()
        logger.warning("Lead soft deleted lead_id=%s", lead_id)
