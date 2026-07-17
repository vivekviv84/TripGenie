from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.container import get_google_sheets_service
from app.core.config import get_settings
from app.db.dependencies import get_db
from app.schemas.monitoring import HealthResponse
from app.services.monitoring import MonitoringService

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)) -> HealthResponse:
    """Return application, database, and Google Sheets health."""

    return MonitoringService(db, get_settings(), get_google_sheets_service()).health()


@router.get("/ready")
def readiness_check(response: Response, db: Session = Depends(get_db)) -> dict[str, str]:
    """Return whether the application is ready to serve traffic."""

    ready = MonitoringService(db, get_settings(), get_google_sheets_service()).ready()
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not_ready"}
    return {"status": "ready"}


@router.get("/live")
def liveness_check() -> dict[str, str]:
    """Return a cheap liveness check."""

    return MonitoringService.live()
