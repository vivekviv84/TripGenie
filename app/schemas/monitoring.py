from datetime import datetime

from pydantic import BaseModel


class ComponentStatus(BaseModel):
    """Status for an external or internal runtime dependency."""

    status: str
    detail: str | None = None


class HealthResponse(BaseModel):
    """Production health response."""

    status: str
    database: ComponentStatus
    google_sheets: ComponentStatus
    version: str
    timestamp: datetime
