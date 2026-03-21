#!/usr/bin/env python3
"""
Example script to test database connection without requiring SECRET_KEY or S3 settings.

This demonstrates that database connection works independently of JWT/authentication/S3 settings.
"""

import os
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Load environment variables from .env file
load_dotenv()


def get_database_url():
    """Construct database URL from environment variables."""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    # Build from individual components
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    db = os.getenv("DB_NAME", "fixing_service_db")
    driver = os.getenv("DB_DRIVER", "psycopg2")

    if password:
        auth = f"{user}:{password}@"
    else:
        auth = f"{user}@"

    return f"postgresql+{driver}://{auth}{host}:{port}/{db}"


@contextmanager
def session_scope(engine):
    """Context manager that yields a session and ensures it is closed."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def test_database_connection():
    """Test database connection without SECRET_KEY or S3 settings."""
    print("Testing database connection...")
    print("Note: SECRET_KEY and S3 settings are NOT required for database connection.\n")

    database_url = get_database_url()
    engine = create_engine(database_url)

    try:
        with session_scope(engine) as session:
            result = session.execute(text("SELECT version()"))
            version = result.scalar()
            print("✅ Database connection successful!")
            print(f"   PostgreSQL version: {version}\n")

            # Test query
            result = session.execute(text("SELECT current_database()"))
            db_name = result.scalar()
            print(f"✅ Connected to database: {db_name}\n")

            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}\n")
        print("Make sure:")
        print("  1. PostgreSQL is running")
        print("  2. Database credentials are set in .env file")
        print("  3. Database exists")
        return False


if __name__ == "__main__":
    success = test_database_connection()
    exit(0 if success else 1)

