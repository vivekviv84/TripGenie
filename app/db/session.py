from collections.abc import Generator

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def create_database_engine(settings: Settings | None = None) -> Engine:
    """Create the SQLAlchemy engine for PostgreSQL."""

    resolved_settings = settings or get_settings()
    return create_engine(
        resolved_settings.sqlalchemy_database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        future=True,
    )


engine = create_database_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    future=True,
)


def get_db_session() -> Generator[Session, None, None]:
    """Yield a database session and always close it after request handling."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_database_connection() -> None:
    """Fail fast when the configured PostgreSQL database is unreachable."""

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Database connection verified")
    except Exception:
        logger.exception("Database connection verification failed")
        raise
