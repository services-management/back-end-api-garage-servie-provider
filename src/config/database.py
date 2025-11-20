from typing import Generator, Optional
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from src.config.settings import settings


class Database:
    """Encapsulates SQLAlchemy engine, session maker and Base.

    Usage:
      db = Database()
      with db.session_scope() as session:
          ...

    Provides a `get_db()` generator function used as a FastAPI dependency.
    """

    def __init__(self, database_url: Optional[str] = None, **engine_kwargs):
        self.database_url = database_url or settings.DATABASE_URL
        # allow caller to override engine kwargs (pooling, echo, etc.)
        self.engine = create_engine(self.database_url, **engine_kwargs)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.Base = declarative_base()

    def get_db(self) -> Generator:
        """Yield a SQLAlchemy Session (generator for FastAPI dependency)."""
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
    """Module-level generator for FastAPI dependencies.

    Keeps compatibility with existing imports that expect a `get_db` function.
    """
    yield from default_db.get_db()
