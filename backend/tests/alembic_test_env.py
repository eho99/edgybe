"""
Test-specific Alembic environment for running migrations in SQLite.

This module handles SQLite compatibility by using Base.metadata.create_all()
which works with SQLAlchemy's enum handling (create_type=False means enums
are stored as strings in SQLite).
"""
import os
import sys
from pathlib import Path
from sqlalchemy import event
from sqlalchemy.engine import Engine

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Import models to ensure they're registered
from app.db import Base
from app.models import *  # Import all models


def upgrade_database(engine):
    """
    Create database tables for testing.
    
    For SQLite testing, we use Base.metadata.create_all() instead of running
    Alembic migrations because:
    1. SQLite doesn't support PostgreSQL enums - SQLAlchemy handles this by
       storing enums as strings when create_type=False (which our models use)
    2. The migrations contain PostgreSQL-specific SQL that won't work in SQLite
    3. Base.metadata.create_all() creates the correct schema for SQLite
    
    This approach is simpler and more reliable for testing.
    """
    # Enable foreign key constraints in SQLite (they're disabled by default)
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    # Create all tables
    Base.metadata.create_all(bind=engine)

