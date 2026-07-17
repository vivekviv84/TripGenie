from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from gspread.exceptions import GSpreadException
from sqlalchemy.exc import SQLAlchemyError

from app.core.logging import get_logger

logger = get_logger(__name__)


class ApplicationError(Exception):
    """Base exception for expected application-level failures."""

    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class LeadProcessingError(ApplicationError):
    """Raised when a lead webhook cannot be processed safely."""


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    """Build a consistent JSON error response."""

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
            }
        },
    )


async def application_error_handler(request: Request, exc: ApplicationError) -> JSONResponse:
    """Return sanitized responses for expected application errors."""

    logger.warning("Application error on %s: %s", request.url.path, exc.message)
    return _error_response(exc.status_code, "application_error", exc.message)


async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Return sanitized responses for HTTP exceptions such as authentication failures."""

    logger.warning("HTTP error on %s status_code=%s", request.url.path, exc.status_code)
    message = exc.detail if isinstance(exc.detail, str) else "Request failed"
    return _error_response(exc.status_code, "http_error", message)


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Return a stable validation response without exposing internals."""

    logger.warning("Validation error on %s with %s issue(s)", request.url.path, len(exc.errors()))
    return _error_response(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        "validation_error",
        "Request payload failed validation",
    )


async def database_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Return a sanitized response for database failures."""

    logger.exception("Database error on %s", request.url.path)
    return _error_response(
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "database_error",
        "Database temporarily unavailable",
    )


async def google_sheets_error_handler(request: Request, exc: GSpreadException) -> JSONResponse:
    """Return a sanitized response for Google Sheets failures."""

    logger.exception("Google Sheets error on %s", request.url.path)
    return _error_response(
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "google_sheets_error",
        "Google Sheets temporarily unavailable",
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return a generic response for unexpected failures."""

    logger.exception("Unhandled error on %s", request.url.path)
    return _error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "internal_error",
        "Internal server error",
    )
