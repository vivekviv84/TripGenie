from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from gspread.exceptions import GSpreadException
from sqlalchemy.exc import SQLAlchemyError

from app.api.router import api_router
from app.core.container import get_google_sheets_service
from app.core.config import get_settings
from app.core.exceptions import (
    ApplicationError,
    application_error_handler,
    database_error_handler,
    google_sheets_error_handler,
    http_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestLoggingMiddleware
from app.db.session import verify_database_connection


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Run startup and shutdown hooks for the FastAPI application."""

    settings = get_settings()
    configure_logging(settings.log_level)
    logger = get_logger(__name__)

    logger.info("Starting %s in %s mode", settings.app_name, settings.app_env)
    verify_database_connection()
    try:
        get_google_sheets_service().verify_connection()
    except Exception:
        logger.warning("Google Sheets unavailable at startup; continuing in degraded mode")

    yield

    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""

    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.app_debug,
        lifespan=lifespan,
    )
    app.add_middleware(RequestLoggingMiddleware)
    app.add_exception_handler(ApplicationError, application_error_handler)
    app.add_exception_handler(HTTPException, http_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(SQLAlchemyError, database_error_handler)
    app.add_exception_handler(GSpreadException, google_sheets_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
