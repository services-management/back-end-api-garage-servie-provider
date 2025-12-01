#!/usr/bin/env python3
"""
Example script to test database connection without requiring SECRET_KEY.

This demonstrates that database connection works independently of JWT/authentication settings.
"""

import sys
import os

# Add parent directory to path to import from src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.database import Database, get_db
from sqlalchemy import text


def test_database_connection():
    """Test database connection without SECRET_KEY."""
    print("Testing database connection...")
    print("Note: SECRET_KEY is NOT required for database connection.\n")
    
    # Create database instance
    db = Database()
    
    # Test connection using session_scope
    try:
        with db.session_scope() as session:
            result = session.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Database connection successful!")
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
    sys.exit(0 if success else 1)

