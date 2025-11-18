import pytest
from fastapi.testclient import TestClient
import uuid

from app.models import Profile, OrganizationMember, StudentGuardian, Organization, GuardianRelationType, OrgRole, MemberStatus


mock_admin_uuid = uuid.UUID("190fa60a-1ff1-4fa0-abc3-ffac2ed211b1")
mock_org_uuid = uuid.UUID("390fa60a-1ff1-4fa0-abc3-ffac2ed211b1")
mock_guardian_uuid = uuid.UUID("490fa60a-1ff1-4fa0-abc3-ffac2ed211b1")
mock_student_uuid = uuid.UUID("590fa60a-1ff1-4fa0-abc3-ffac2ed211b1")


@pytest.fixture(autouse=True)
def setup_test_data(db_session, mock_user):
    """Setup test data for each test."""
    # Use mock_user as admin
    test_org = Organization(id=mock_org_uuid, name="Test Organization")
    db_session.add(test_org)
    
    # Create admin member
    admin_member = OrganizationMember(
        organization_id=mock_org_uuid,
        user_id=mock_user.id,
        role=OrgRole.admin,
        status=MemberStatus.active
    )
    db_session.add(admin_member)
    
    # Create guardian and student profiles
    guardian_profile = Profile(id=mock_guardian_uuid, full_name="Guardian User")
    student_profile = Profile(id=mock_student_uuid, full_name="Student User")
    db_session.add_all([guardian_profile, student_profile])
    
    # Create guardian and student members
    guardian_member = OrganizationMember(
        organization_id=mock_org_uuid,
        user_id=mock_guardian_uuid,
        role=OrgRole.guardian,
        status=MemberStatus.active
    )
    student_member = OrganizationMember(
        organization_id=mock_org_uuid,
        user_id=mock_student_uuid,
        role=OrgRole.student,
        status=MemberStatus.active
    )
    db_session.add_all([guardian_member, student_member])
    db_session.commit()
    yield
    # Cleanup is handled by db_session fixture


def test_create_guardian_student_link(client: TestClient, db_session):
    """Test creating a guardian-student link"""
    link_data = {
        "guardian_id": str(mock_guardian_uuid),
        "student_id": str(mock_student_uuid),
        "relationship_type": "primary"
    }
    url = f"/api/v1/organizations/{mock_org_uuid}/guardians/link"
    response = client.post(url, json=link_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["guardian_id"] == str(mock_guardian_uuid)
    assert data["student_id"] == str(mock_student_uuid)
    assert data["relationship_type"] == "primary"
    
    # Verify in DB
    link = db_session.query(StudentGuardian).filter(
        StudentGuardian.organization_id == mock_org_uuid,
        StudentGuardian.guardian_id == mock_guardian_uuid,
        StudentGuardian.student_id == mock_student_uuid
    ).first()
    assert link is not None
    assert link.relationship_type == GuardianRelationType.primary


def test_get_student_guardians(client: TestClient, db_session):
    """Test getting all guardians for a student"""
    # Create a link first
    link = StudentGuardian(
        organization_id=mock_org_uuid,
        guardian_id=mock_guardian_uuid,
        student_id=mock_student_uuid,
        relationship_type=GuardianRelationType.primary
    )
    db_session.add(link)
    db_session.commit()

    url = f"/api/v1/organizations/{mock_org_uuid}/students/{mock_student_uuid}/guardians"
    response = client.get(url)
    
    assert response.status_code == 200
    data = response.json()
    assert data["student"]["id"] == str(mock_student_uuid)
    assert isinstance(data["guardians"], list)
    assert len(data["guardians"]) == 1
    guardian_entry = data["guardians"][0]
    assert guardian_entry["guardian_id"] == str(mock_guardian_uuid)
    assert guardian_entry["relationship_type"] == "primary"


def test_get_guardian_students(client: TestClient, db_session):
    """Test getting all students for a guardian"""
    # Create a link first
    link = StudentGuardian(
        organization_id=mock_org_uuid,
        guardian_id=mock_guardian_uuid,
        student_id=mock_student_uuid,
        relationship_type=GuardianRelationType.primary
    )
    db_session.add(link)
    db_session.commit()

    url = f"/api/v1/organizations/{mock_org_uuid}/guardians/{mock_guardian_uuid}/students"
    response = client.get(url)
    
    assert response.status_code == 200
    data = response.json()
    assert data["guardian"]["id"] == str(mock_guardian_uuid)
    assert isinstance(data["students"], list)
    assert len(data["students"]) == 1
    student_entry = data["students"][0]
    assert student_entry["student_id"] == str(mock_student_uuid)
    assert student_entry["relationship_type"] == "primary"


def test_delete_guardian_student_link(client: TestClient, db_session):
    """Test deleting a guardian-student link"""
    # Create a link first
    link = StudentGuardian(
        organization_id=mock_org_uuid,
        guardian_id=mock_guardian_uuid,
        student_id=mock_student_uuid,
        relationship_type=GuardianRelationType.primary
    )
    db_session.add(link)
    db_session.commit()

    url = f"/api/v1/organizations/{mock_org_uuid}/guardians/link"
    response = client.delete(
        url,
        params={
            "guardian_id": str(mock_guardian_uuid),
            "student_id": str(mock_student_uuid)
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "removed" in data["message"].lower() or "success" in data["message"].lower()
    
    # Verify removed from DB
    link = db_session.query(StudentGuardian).filter(
        StudentGuardian.organization_id == mock_org_uuid,
        StudentGuardian.guardian_id == mock_guardian_uuid,
        StudentGuardian.student_id == mock_student_uuid
    ).first()
    assert link is None


def test_duplicate_relationship_prevention(client: TestClient, db_session):
    """Test that duplicate relationships are prevented"""
    link_data = {
        "guardian_id": str(mock_guardian_uuid),
        "student_id": str(mock_student_uuid),
        "relationship_type": "primary"
    }
    url = f"/api/v1/organizations/{mock_org_uuid}/guardians/link"
    
    # Create first link
    response1 = client.post(url, json=link_data)
    assert response1.status_code == 200
    
    # Try to create duplicate
    response2 = client.post(url, json=link_data)
    assert response2.status_code == 400
    assert "already exists" in response2.json().get("detail", "").lower()


def test_link_guardian_not_in_org(client: TestClient, db_session):
    """Test that linking fails if guardian is not in organization"""
    # Create a guardian in a different org
    other_org = Organization(id=uuid.uuid4(), name="Other Organization")
    db_session.add(other_org)
    
    other_guardian_id = uuid.uuid4()
    other_guardian_profile = Profile(id=other_guardian_id, full_name="Other Guardian")
    db_session.add(other_guardian_profile)
    
    other_guardian_member = OrganizationMember(
        organization_id=other_org.id,
        user_id=other_guardian_id,
        role=OrgRole.guardian,
        status=MemberStatus.active
    )
    db_session.add(other_guardian_member)
    db_session.commit()
    
    link_data = {
        "guardian_id": str(other_guardian_id),
        "student_id": str(mock_student_uuid),
        "relationship_type": "primary"
    }
    url = f"/api/v1/organizations/{mock_org_uuid}/guardians/link"
    response = client.post(url, json=link_data)
    
    assert response.status_code == 404
    assert "guardian" in response.json()["detail"].lower()


def test_link_student_not_in_org(client: TestClient, db_session):
    """Test that linking fails if student is not in organization"""
    # Create a student in a different org
    other_org = Organization(id=uuid.uuid4(), name="Other Organization")
    db_session.add(other_org)
    
    other_student_id = uuid.uuid4()
    other_student_profile = Profile(id=other_student_id, full_name="Other Student")
    db_session.add(other_student_profile)
    
    other_student_member = OrganizationMember(
        organization_id=other_org.id,
        user_id=other_student_id,
        role=OrgRole.student,
        status=MemberStatus.active
    )
    db_session.add(other_student_member)
    db_session.commit()
    
    link_data = {
        "guardian_id": str(mock_guardian_uuid),
        "student_id": str(other_student_id),
        "relationship_type": "primary"
    }
    url = f"/api/v1/organizations/{mock_org_uuid}/guardians/link"
    response = client.post(url, json=link_data)
    
    assert response.status_code == 404
    assert "student" in response.json()["detail"].lower()


def test_delete_nonexistent_link(client: TestClient):
    """Test deleting a link that doesn't exist"""
    url = f"/api/v1/organizations/{mock_org_uuid}/guardians/link"
    response = client.delete(
        url,
        params={
            "guardian_id": str(mock_guardian_uuid),
            "student_id": str(mock_student_uuid)
        }
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
