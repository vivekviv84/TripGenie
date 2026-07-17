from collections.abc import Generator

from sqlalchemy.orm import Session

from app.db.session import get_db_session


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that provides one SQLAlchemy session per request."""

    yield from get_db_session()
