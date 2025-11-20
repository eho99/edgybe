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

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Import Base first
from app.db import Base

# Explicitly import all models to ensure they're registered with Base.metadata
# This must happen at module import time, not inside the function
from app.models.organization import Organization
from app.models.profile import Profile
from app.models.organization_member import OrganizationMember
from app.models.student_guardian import StudentGuardian
from app.models.invitation import Invitation

# Also import via the models package to ensure everything is loaded
from app.models import (
    Organization as OrgModel,
    Profile as ProfileModel,
    OrganizationMember as OrgMemberModel,
    StudentGuardian as StudentGuardianModel,
    Invitation as InvitationModel
)

# Track which engines have had the pragma registered
_registered_engines = set()


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
    # Ensure all models are imported before creating tables
    # This is important when the module is loaded dynamically via importlib
    try:
        from app.models.organization import Organization
        from app.models.profile import Profile
        from app.models.organization_member import OrganizationMember
        from app.models.student_guardian import StudentGuardian
        from app.models.invitation import Invitation
    except ImportError:
        # If direct imports fail, try importing from the package
        from app.models import Organization, Profile, OrganizationMember, StudentGuardian, Invitation
    
    # Register SQLite foreign key pragma for this engine (only once per engine)
    if id(engine) not in _registered_engines:
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            """Enable foreign key constraints in SQLite."""
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        _registered_engines.add(id(engine))
    
    # Drop all tables first to ensure clean state
    # This is safe because we're in a test environment
    # checkfirst=True means it won't error if tables don't exist
    Base.metadata.drop_all(bind=engine, checkfirst=True)
    
    # Create all tables - models should now be registered
    # checkfirst=True means it won't error if tables already exist
    Base.metadata.create_all(bind=engine, checkfirst=True)

