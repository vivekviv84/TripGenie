from functools import lru_cache

from app.core.config import get_settings
from app.services.background_sync import BackgroundLeadSyncService
from app.services.google_sheets import GoogleSheetsService
from app.services.lead_scoring import LeadScoringService


@lru_cache(maxsize=1)
def get_google_sheets_service() -> GoogleSheetsService:
    """Return a cached Google Sheets service."""

    return GoogleSheetsService(get_settings())


@lru_cache(maxsize=1)
def get_background_lead_sync_service() -> BackgroundLeadSyncService:
    """Return a cached background sync wrapper."""

    return BackgroundLeadSyncService(get_google_sheets_service())


@lru_cache(maxsize=1)
def get_lead_scoring_service() -> LeadScoringService:
    """Return a cached lead scoring service."""

    return LeadScoringService(get_settings())
