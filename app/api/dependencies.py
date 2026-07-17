from secrets import compare_digest
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.container import get_background_lead_sync_service, get_lead_scoring_service
from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.dependencies import get_db
from app.repositories.lead_repository import LeadRepository
from app.services.lead_processing import LeadProcessingService

logger = get_logger(__name__)


def authenticate_webhook_request(
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> None:
    """Authenticate webhook requests using a shared API key."""

    settings = get_settings()
    configured_key = settings.webhook_api_key

    if not x_api_key or not compare_digest(x_api_key, configured_key):
        logger.warning("Webhook authentication failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )

    logger.info("Webhook request authenticated")


def authenticate_operations_request(
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> None:
    """Authenticate internal lead management and analytics requests."""

    settings = get_settings()
    if not x_api_key or not compare_digest(x_api_key, settings.operations_api_key):
        logger.warning("Operations authentication failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )


def get_lead_processing_service(db: Session = Depends(get_db)) -> LeadProcessingService:
    """Build the lead processing service with database and sync dependencies."""

    repository = LeadRepository(db)
    return LeadProcessingService(
        lead_repository=repository,
        lead_scoring_service=get_lead_scoring_service(),
        lead_sync_service=get_background_lead_sync_service(),
    )
