import pytest
from dotenv import load_dotenv
import sys
import os
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import uuid

# Add the backend directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.db import Base, get_db
from app import schemas
from app.models.organization_member import OrgRole

# Import test migration helper
# Import directly since the file is in the same directory
import importlib.util
alembic_test_env_path = os.path.join(os.path.dirname(__file__), "alembic_test_env.py")
spec = importlib.util.spec_from_file_location("alembic_test_env", alembic_test_env_path)
alembic_test_env = importlib.util.module_from_spec(spec)
spec.loader.exec_module(alembic_test_env)
upgrade_database = alembic_test_env.upgrade_database

@pytest.fixture(scope='session', autouse=True)
def load_test_env():
    load_dotenv(dotenv_path='backend/.env.test')

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test with migrations applied."""
    # Drop all tables first to ensure clean state
    Base.metadata.drop_all(bind=engine)
    
    # Run migrations/create tables
    upgrade_database(engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Clean up after test
        Base.metadata.drop_all(bind=engine)

# ============================================================================
# Auth Mocking Fixtures
# ============================================================================

@pytest.fixture
def mock_user():
    """Create a mock SupabaseUser for testing."""
    return schemas.SupabaseUser(
        id=uuid.UUID("190fa60a-1ff1-4fa0-abc3-ffac2ed211b1"),
        email="test@example.com"
    )

@pytest.fixture
def mock_user_admin():
    """Create a mock SupabaseUser with admin role context."""
    return schemas.SupabaseUser(
        id=uuid.UUID("190fa60a-1ff1-4fa0-abc3-ffac2ed211b1"),
        email="admin@example.com"
    )

@pytest.fixture
def mock_authenticated_member(mock_user):
    """Create a mock AuthenticatedMember for testing."""
    org_id = uuid.UUID("390fa60a-1ff1-4fa0-abc3-ffac2ed211b1")
    return schemas.AuthenticatedMember(
        user=mock_user,
        org_id=org_id,
        role=OrgRole.admin
    )

@pytest.fixture
def mock_authenticated_member_staff(mock_user):
    """Create a mock AuthenticatedMember with staff role."""
    org_id = uuid.UUID("390fa60a-1ff1-4fa0-abc3-ffac2ed211b1")
    return schemas.AuthenticatedMember(
        user=mock_user,
        org_id=org_id,
        role=OrgRole.staff
    )

@pytest.fixture
def mock_authenticated_member_secretary(mock_user):
    """Create a mock AuthenticatedMember with secretary role."""
    org_id = uuid.UUID("390fa60a-1ff1-4fa0-abc3-ffac2ed211b1")
    return schemas.AuthenticatedMember(
        user=mock_user,
        org_id=org_id,
        role=OrgRole.secretary
    )

# ============================================================================
# Supabase Client Mocking
# ============================================================================

@pytest.fixture(scope="function", autouse=True)
def mock_supabase_client():
    """Mock Supabase client for testing - automatically applied to all tests."""
    mock_client = MagicMock()
    mock_auth = MagicMock()
    mock_admin = MagicMock()
    
    # Set up the mock structure
    mock_client.auth = mock_auth
    mock_auth.admin = mock_admin
    
    # Mock common auth operations
    mock_user_response = MagicMock()
    mock_user = MagicMock()
    mock_user.id = str(uuid.UUID("190fa60a-1ff1-4fa0-abc3-ffac2ed211b1"))
    mock_user.email = "test@example.com"
    mock_user_response.user = mock_user
    mock_auth.get_user = MagicMock(return_value=mock_user_response)
    
    # Mock admin operations
    mock_admin.list_users = MagicMock(return_value=[])
    mock_admin.invite_user_by_email = MagicMock(return_value={"email": "test@example.com"})
    
    # Mock password reset
    mock_auth.reset_password_for_email = MagicMock(return_value=None)
    
    # Patch the supabase client in all places it's used
    # Note: routers import supabase from app.auth inside functions, so we only need to patch app.auth.supabase
    with patch('app.auth.supabase', mock_client):
        with patch('app.services.invitations.supabase', mock_client):
            yield mock_client

# ============================================================================
# Test Client with Auth Overrides
# ============================================================================

@pytest.fixture(scope="function")
def client(db_session, mock_user):
    """Create a test client with database session and auth overrides."""
    from app.auth import get_current_user, get_current_active_member, get_user_organizations, get_user_default_organization
    from app.auth import require_admin_role, require_admin_or_secretary_role, require_active_role
    from fastapi import Request, Depends
    from pydantic import UUID4
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    async def override_get_current_user(credentials=None):
        """Override get_current_user - returns mock_user without checking token."""
        # credentials parameter is ignored since we're mocking auth
        return mock_user
    
    async def override_get_current_active_member(
        request: Request,
        org_id: UUID4,
        db=Depends(get_db),
        user=Depends(get_current_user)
    ):
        """Mock get_current_active_member - returns member if exists in DB, otherwise raises 403."""
        from app.models.organization_member import OrganizationMember, MemberStatus
        from fastapi import HTTPException
        
        # FastAPI will resolve get_db and get_current_user using our overrides
        # But we want to ensure we use our test db_session and mock_user
        db = db_session
        user = mock_user
        
        # Ensure org_id is a UUID object (FastAPI may pass it as a Pydantic UUID4 or string)
        if isinstance(org_id, str):
            org_id = uuid.UUID(org_id)
        elif hasattr(org_id, '__str__') and not isinstance(org_id, uuid.UUID):
            # Handle Pydantic UUID4 or other UUID-like objects
            org_id = uuid.UUID(str(org_id))
        
        # Ensure user.id is a UUID object
        user_id = user.id
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        elif hasattr(user_id, '__str__') and not isinstance(user_id, uuid.UUID):
            user_id = uuid.UUID(str(user_id))
        
        member = db.query(OrganizationMember).filter(
            OrganizationMember.user_id == user_id,
            OrganizationMember.organization_id == org_id
        ).first()
        
        if not member:
            raise HTTPException(status_code=403, detail="User not a member of this organization")
        
        if member.status != MemberStatus.active:
            raise HTTPException(status_code=403, detail="User is inactive in this organization")
        
        return schemas.AuthenticatedMember(
            user=user,
            org_id=member.organization_id,
            role=member.role
        )
    
    async def override_get_user_organizations(db=None, user=None):
        """Mock get_user_organizations - returns memberships from DB."""
        if db is None:
            db = db_session
        if user is None:
            user = mock_user
        
        from app.models.organization_member import OrganizationMember, MemberStatus
        
        memberships = db.query(OrganizationMember).join(
            OrganizationMember.organization
        ).filter(
            OrganizationMember.user_id == user.id,
            OrganizationMember.status == MemberStatus.active
        ).all()
        
        result = []
        for membership in memberships:
            result.append(schemas.OrganizationMembership(
                org_id=membership.organization_id,
                role=membership.role,
                organization_name=membership.organization.name,
                joined_at=membership.joined_at
            ))
        
        return result
    
    async def override_get_user_default_organization(db=None, user=None):
        """Mock get_user_default_organization - returns first active membership."""
        if db is None:
            db = db_session
        if user is None:
            user = mock_user
        
        from app.models.organization_member import OrganizationMember, MemberStatus
        from fastapi import HTTPException
        
        membership = db.query(OrganizationMember).join(
            OrganizationMember.organization
        ).filter(
            OrganizationMember.user_id == user.id,
            OrganizationMember.status == MemberStatus.active
        ).first()
        
        if not membership:
            raise HTTPException(status_code=403, detail="User is not a member of any organization")
        
        return schemas.AuthenticatedMember(
            user=user,
            org_id=membership.organization_id,
            role=membership.role
        )
    
    # Override dependencies
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_active_member] = override_get_current_active_member
    app.dependency_overrides[get_user_organizations] = override_get_user_organizations
    app.dependency_overrides[get_user_default_organization] = override_get_user_default_organization
    
    # Role-based dependencies depend on get_current_active_member, so they'll work automatically
    # But we can override them if needed for specific tests
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up overrides
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def client_without_auth(db_session):
    """Create a test client without auth overrides - for testing auth endpoints."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
