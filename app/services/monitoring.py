from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.schemas.monitoring import ComponentStatus, HealthResponse
from app.services.google_sheets import GoogleSheetsService


class MonitoringService:
    """Runtime health and readiness checks."""

    def __init__(self, db: Session, settings: Settings, google_sheets_service: GoogleSheetsService) -> None:
        self.db = db
        self.settings = settings
        self.google_sheets_service = google_sheets_service

    def health(self) -> HealthResponse:
        """Return application and dependency health."""

        database = self.database_status()
        google_sheets = self.google_sheets_status()
        overall = "ok" if database.status == "ok" and google_sheets.status == "ok" else "degraded"
        return HealthResponse(
            status=overall,
            database=database,
            google_sheets=google_sheets,
            version=self.settings.app_version,
            timestamp=datetime.now(timezone.utc),
        )

    def ready(self) -> bool:
        """Return whether the app is ready to serve traffic."""

        return self.database_status().status == "ok"

    @staticmethod
    def live() -> dict[str, str]:
        """Return a cheap liveness response."""

        return {"status": "alive"}

    def database_status(self) -> ComponentStatus:
        """Check database connectivity."""

        try:
            self.db.execute(text("SELECT 1"))
            return ComponentStatus(status="ok")
        except Exception as exc:
            return ComponentStatus(status="error", detail=exc.__class__.__name__)

    def google_sheets_status(self) -> ComponentStatus:
        """Check Google Sheets connectivity."""

        try:
            self.google_sheets_service.verify_connection()
            return ComponentStatus(status="ok")
        except Exception as exc:
            return ComponentStatus(status="error", detail=exc.__class__.__name__)
