from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import authenticate_operations_request
from app.db.dependencies import get_db
from app.repositories.lead_repository import LeadRepository
from app.schemas.lead import LeadListResponse, LeadResponse, LeadUpdateRequest
from app.services.lead_management import LeadManagementService

router = APIRouter(prefix="/leads", tags=["leads"], dependencies=[Depends(authenticate_operations_request)])


@router.get("", response_model=LeadListResponse)
def list_leads(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    priority: str | None = None,
    destination: str | None = None,
    search: str | None = None,
    sort_by: Literal["created_at", "updated_at", "lead_score", "budget", "customer_name"] = "created_at",
    sort_order: Literal["asc", "desc"] = "desc",
    db: Session = Depends(get_db),
) -> LeadListResponse:
    """Return paginated leads with filtering, sorting, and search."""

    service = LeadManagementService(LeadRepository(db))
    return service.list_leads(
        page=page,
        page_size=page_size,
        status_filter=status_filter,
        priority=priority,
        destination=destination,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/{lead_id}", response_model=LeadResponse)
def get_lead(lead_id: UUID, db: Session = Depends(get_db)) -> LeadResponse:
    """Return one lead by id."""

    return LeadManagementService(LeadRepository(db)).get_lead(lead_id)


@router.put("/{lead_id}", response_model=LeadResponse)
def update_lead(
    lead_id: UUID,
    request: LeadUpdateRequest,
    db: Session = Depends(get_db),
) -> LeadResponse:
    """Update consultant-editable lead fields."""

    return LeadManagementService(LeadRepository(db)).update_lead(lead_id, request)


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(lead_id: UUID, db: Session = Depends(get_db)) -> None:
    """Soft delete a lead."""

    LeadManagementService(LeadRepository(db)).delete_lead(lead_id)
