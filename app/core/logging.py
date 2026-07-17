import logging
import json
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """Small JSON-style formatter for production-friendly logs."""

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        timestamp = datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()
        return json.dumps(
            {
                "timestamp": timestamp,
                "level": record.levelname,
                "logger": record.name,
                "message": message,
            }
        )


def configure_logging(log_level: str) -> None:
    """Configure application-wide structured-enough console logging."""

    logging.basicConfig(
        level=log_level.upper(),
        handlers=[_console_handler()],
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    """Return a named logger for consistent usage across future services."""

    return logging.getLogger(name)


def _console_handler() -> logging.StreamHandler:
    """Create a stdout handler with structured formatting."""

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter("%(message)s"))
    return handler
