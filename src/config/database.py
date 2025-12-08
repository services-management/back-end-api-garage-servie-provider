from typing import Generator, Optional
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.config.settings import settings


class Database:
    """Encapsulates SQLAlchemy engine, session maker and Base.

    Note: Database connection works independently of SECRET_KEY.
    Only DATABASE_URL (or DB_USER, DB_PASSWORD, etc.) is required.

    Usage:
      db = Database()
      with db.session_scope() as session:
          ...

    Provides a `get_db()` generator function used as a FastAPI dependency.
    """

    def __init__(self, database_url: Optional[str] = None, **engine_kwargs):
        """Initialize database connection."""

        self.database_url = database_url or settings.DATABASE_URL
        # allow caller to override engine kwargs (pooling, echo, etc.)
        self.engine = create_engine(self.database_url, **engine_kwargs)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.Base = declarative_base()

    def get_db(self) -> Generator:
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    @contextmanager
    def session_scope(self):
        """Context manager that yields a session and ensures it is closed.

        It rolls back on exception. It does not auto-commit; commit should be
        performed by the caller when appropriate.
        """
        db = self.SessionLocal()
        try:
            yield db
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()


# Default, module-level instance for convenience and backwards compatibility
default_db = Database()

engine = default_db.engine
SessionLocal = default_db.SessionLocal
Base = default_db.Base

def get_db():
    yield from default_db.get_db()
