from functools import lru_cache
from pathlib import Path

from pydantic import Field, PostgresDsn, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = Field(default="TripGenie AI Backend", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    app_env: str = Field(default="local", alias="APP_ENV")
    app_debug: bool = Field(default=False, alias="APP_DEBUG")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    database_url: PostgresDsn = Field(alias="DATABASE_URL")
    webhook_api_key: str = Field(alias="WEBHOOK_API_KEY", min_length=16)
    operations_api_key: str = Field(alias="OPERATIONS_API_KEY", min_length=16)
    google_sheets_enabled: bool = Field(default=True, alias="GOOGLE_SHEETS_ENABLED")
    google_sheet_id: str | None = Field(default=None, alias="GOOGLE_SHEET_ID")
    google_worksheet: str | None = Field(default=None, alias="GOOGLE_WORKSHEET")
    google_service_account_file: Path | None = Field(default=None, alias="GOOGLE_SERVICE_ACCOUNT_FILE")
    lead_hot_threshold: int = Field(default=75, alias="LEAD_HOT_THRESHOLD", ge=0, le=100)
    lead_warm_threshold: int = Field(default=45, alias="LEAD_WARM_THRESHOLD", ge=0, le=100)
    lead_high_intent_threshold: int = Field(default=70, alias="LEAD_HIGH_INTENT_THRESHOLD", ge=0, le=100)
    lead_medium_intent_threshold: int = Field(default=40, alias="LEAD_MEDIUM_INTENT_THRESHOLD", ge=0, le=100)
    lead_realistic_budget_min: int = Field(default=50000, alias="LEAD_REALISTIC_BUDGET_MIN", ge=0)
    lead_score_weight_destination: int = Field(default=15, alias="LEAD_SCORE_WEIGHT_DESTINATION", ge=0, le=100)
    lead_score_weight_travel_month: int = Field(default=15, alias="LEAD_SCORE_WEIGHT_TRAVEL_MONTH", ge=0, le=100)
    lead_score_weight_travellers: int = Field(default=10, alias="LEAD_SCORE_WEIGHT_TRAVELLERS", ge=0, le=100)
    lead_score_weight_budget_available: int = Field(default=15, alias="LEAD_SCORE_WEIGHT_BUDGET_AVAILABLE", ge=0, le=100)
    lead_score_weight_budget_realistic: int = Field(default=10, alias="LEAD_SCORE_WEIGHT_BUDGET_REALISTIC", ge=0, le=100)
    lead_score_weight_customer_intent: int = Field(default=15, alias="LEAD_SCORE_WEIGHT_CUSTOMER_INTENT", ge=0, le=100)
    lead_score_weight_trip_type: int = Field(default=10, alias="LEAD_SCORE_WEIGHT_TRIP_TYPE", ge=0, le=100)
    lead_score_weight_additional_requirements: int = Field(
        default=10,
        alias="LEAD_SCORE_WEIGHT_ADDITIONAL_REQUIREMENTS",
        ge=0,
        le=100,
    )
    analytics_cache_ttl_seconds: int = Field(default=30, alias="ANALYTICS_CACHE_TTL_SECONDS", ge=0, le=3600)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def sqlalchemy_database_url(self) -> str:
        """Return the database URL in the string format expected by SQLAlchemy."""

        url = str(self.database_url)
        # Force the psycopg 3 driver (psycopg[binary] is installed, not psycopg2).
        if url.startswith("postgresql+psycopg://"):
            return url
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+psycopg://", 1)
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+psycopg://", 1)
        return url

    @field_validator("google_sheet_id")
    @classmethod
    def validate_google_sheet_id(cls, value: str | None) -> str | None:
        """Validate configured Google Sheet id when provided."""

        if value is not None and len(value) < 10:
            raise ValueError("GOOGLE_SHEET_ID must be at least 10 characters")
        return value

    @field_validator("google_worksheet")
    @classmethod
    def validate_google_worksheet(cls, value: str | None) -> str | None:
        """Validate configured Google worksheet when provided."""

        if value is not None and not value.strip():
            raise ValueError("GOOGLE_WORKSHEET cannot be blank")
        return value

    @field_validator("google_service_account_file")
    @classmethod
    def validate_google_service_account_file(cls, value: Path | None) -> Path | None:
        """Validate the Google service account file path when provided."""

        if value is not None and not value.is_file():
            raise ValueError("GOOGLE_SERVICE_ACCOUNT_FILE must point to an existing file")
        return value

    @model_validator(mode="after")
    def validate_scoring_thresholds(self) -> "Settings":
        """Validate that scoring thresholds are ordered from strongest to weakest."""

        if self.lead_hot_threshold <= self.lead_warm_threshold:
            raise ValueError("LEAD_HOT_THRESHOLD must be greater than LEAD_WARM_THRESHOLD")
        if self.lead_high_intent_threshold <= self.lead_medium_intent_threshold:
            raise ValueError("LEAD_HIGH_INTENT_THRESHOLD must be greater than LEAD_MEDIUM_INTENT_THRESHOLD")
        if self.google_sheets_enabled:
            if not self.google_sheet_id:
                raise ValueError("GOOGLE_SHEET_ID is required when GOOGLE_SHEETS_ENABLED is true")
            if not self.google_worksheet:
                raise ValueError("GOOGLE_WORKSHEET is required when GOOGLE_SHEETS_ENABLED is true")
            if self.google_service_account_file is None:
                raise ValueError("GOOGLE_SERVICE_ACCOUNT_FILE is required when GOOGLE_SHEETS_ENABLED is true")
        total_weight = (
            self.lead_score_weight_destination
            + self.lead_score_weight_travel_month
            + self.lead_score_weight_travellers
            + self.lead_score_weight_budget_available
            + self.lead_score_weight_budget_realistic
            + self.lead_score_weight_customer_intent
            + self.lead_score_weight_trip_type
            + self.lead_score_weight_additional_requirements
        )
        if total_weight != 100:
            raise ValueError("Lead scoring weights must add up to 100")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings so validation happens once per process."""

    return Settings()
