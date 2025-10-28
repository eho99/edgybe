import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.models import Profile, OrganizationMember, StudentGuardian, Organization, GuardianRelationType, OrgRole
from app.auth import get_current_user, require_admin_role, require_any_role
from app.schemas import SupabaseUser, AuthenticatedMember

# Mock data
mock_admin_user = SupabaseUser(
    id="uuid-admin-user", 
    email="admin@example.com"
)

mock_regular_user = SupabaseUser(
    id="uuid-regular-user", 
    email="user@example.com"
)

mock_admin_member = AuthenticatedMember(
    user=mock_admin_user,
    org_id="uuid-test-org",
    role=OrgRole.admin
)

mock_regular_member = AuthenticatedMember(
    user=mock_regular_user,
    org_id="uuid-test-org",
    role=OrgRole.staff
)

# Override dependencies
async def override_get_current_user():
    return mock_admin_user

async def override_require_admin_role():
    return mock_admin_member

async def override_require_any_role():
    return mock_regular_member

app.dependency_overrides[get_current_user] = override_get_current_user
app.dependency_overrides[require_admin_role] = override_require_admin_role
app.dependency_overrides[require_any_role] = override_require_any_role

@pytest.fixture(autouse=True)
def setup_test_data(db_session):
    """Setup test data for each test."""
    # Create test organization
    test_org = Organization(id="uuid-test-org", name="Test Organization")
    
    # Create test profiles
    guardian_profile = Profile(id="uuid-guardian", full_name="Guardian User")
    student_profile = Profile(id="uuid-student", full_name="Student User")
    
    # Create organization members
    guardian_member = OrganizationMember(
        organization_id="uuid-test-org",
        user_id="uuid-guardian",
        role=OrgRole.guardian
    )
    student_member = OrganizationMember(
        organization_id="uuid-test-org",
        user_id="uuid-student",
        role=OrgRole.student
    )
    
    db_session.add_all([test_org, guardian_profile, student_profile, guardian_member, student_member])
    db_session.commit()
    
    yield
    
    # Cleanup
    db_session.query(StudentGuardian).delete()
    db_session.query(OrganizationMember).delete()
    db_session.query(Profile).delete()
    db_session.query(Organization).delete()
    db_session.commit()

def test_create_guardian_student_link(client: TestClient, db_session):
    """Test creating a guardian-student relationship."""
    link_data = {
        "guardian_id": "uuid-guardian",
        "student_id": "uuid-student",
        "relationship_type": "primary"
    }
    
    response = client.post("/api/v1/organizations/uuid-test-org/guardians/link", json=link_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["guardian_id"] == "uuid-guardian"
    assert data["student_id"] == "uuid-student"
    assert data["relationship_type"] == "primary"
    
    # Verify in DB
    link = db_session.query(StudentGuardian).filter(
        StudentGuardian.organization_id == "uuid-test-org",
        StudentGuardian.guardian_id == "uuid-guardian",
        StudentGuardian.student_id == "uuid-student"
    ).first()
    assert link is not None
    assert link.relationship_type == GuardianRelationType.primary

def test_get_student_guardians(client: TestClient, db_session):
    """Test getting guardians for a student."""
    # Create a relationship first
    link = StudentGuardian(
        organization_id="uuid-test-org",
        guardian_id="uuid-guardian",
        student_id="uuid-student",
        relationship_type=GuardianRelationType.primary
    )
    db_session.add(link)
    db_session.commit()
    
    response = client.get("/api/v1/organizations/uuid-test-org/students/uuid-student/guardians")
    
    assert response.status_code == 200
    data = response.json()
    assert data["student"]["id"] == "uuid-student"
    assert len(data["guardians"]) == 1
    assert data["guardians"][0]["guardian_id"] == "uuid-guardian"

def test_get_guardian_students(client: TestClient, db_session):
    """Test getting students for a guardian."""
    # Create a relationship first
    link = StudentGuardian(
        organization_id="uuid-test-org",
        guardian_id="uuid-guardian",
        student_id="uuid-student",
        relationship_type=GuardianRelationType.primary
    )
    db_session.add(link)
    db_session.commit()
    
    response = client.get("/api/v1/organizations/uuid-test-org/guardians/uuid-guardian/students")
    
    assert response.status_code == 200
    data = response.json()
    assert data["guardian"]["id"] == "uuid-guardian"
    assert len(data["students"]) == 1
    assert data["students"][0]["student_id"] == "uuid-student"

def test_delete_guardian_student_link(client: TestClient, db_session):
    """Test removing a guardian-student relationship."""
    # Create a relationship first
    link = StudentGuardian(
        organization_id="uuid-test-org",
        guardian_id="uuid-guardian",
        student_id="uuid-student",
        relationship_type=GuardianRelationType.primary
    )
    db_session.add(link)
    db_session.commit()
    
    response = client.delete(
        "/api/v1/organizations/uuid-test-org/guardians/link",
        params={
            "guardian_id": "uuid-guardian",
            "student_id": "uuid-student"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Relationship removed successfully"
    
    # Verify removed from DB
    link = db_session.query(StudentGuardian).filter(
        StudentGuardian.organization_id == "uuid-test-org",
        StudentGuardian.guardian_id == "uuid-guardian",
        StudentGuardian.student_id == "uuid-student"
    ).first()
    assert link is None

def test_duplicate_relationship_prevention(client: TestClient, db_session):
    """Test that duplicate relationships are prevented."""
    # Create initial relationship
    link_data = {
        "guardian_id": "uuid-guardian",
        "student_id": "uuid-student",
        "relationship_type": "primary"
    }
    
    response1 = client.post("/api/v1/organizations/uuid-test-org/guardians/link", json=link_data)
    assert response1.status_code == 200
    
    # Try to create duplicate
    response2 = client.post("/api/v1/organizations/uuid-test-org/guardians/link", json=link_data)
    assert response2.status_code == 400
    assert "already exists" in response2.json()["detail"]
