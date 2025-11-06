import pytest
from fastapi.testclient import TestClient
import uuid
from app.models import Profile, OrganizationMember, StudentGuardian, Organization, GuardianRelationType, OrgRole

mock_admin_uuid = uuid.UUID("190fa60a-1ff1-4fa0-abc3-ffac2ed211b1")
mock_regular_uuid = uuid.UUID("290fa60a-1ff1-4fa0-abc3-ffac2ed211b1")
mock_org_uuid = uuid.UUID("390fa60a-1ff1-4fa0-abc3-ffac2ed211b1")
mock_guardian_uuid = uuid.UUID("490fa60a-1ff1-4fa0-abc3-ffac2ed211b1")
mock_student_uuid = uuid.UUID("590fa60a-1ff1-4fa0-abc3-ffac2ed211b1")


@pytest.fixture(autouse=True)
def setup_test_data(db_session):
    """Setup test data for each test."""
    test_org = Organization(id=mock_org_uuid, name="Test Organization")
    guardian_profile = Profile(id=mock_guardian_uuid, full_name="Guardian User")
    student_profile = Profile(id=mock_student_uuid, full_name="Student User")
    guardian_member = OrganizationMember(
        organization_id=mock_org_uuid,
        user_id=mock_guardian_uuid,
        role=OrgRole.guardian
    )
    student_member = OrganizationMember(
        organization_id=mock_org_uuid,
        user_id=mock_student_uuid,
        role=OrgRole.student
    )
    db_session.add_all([test_org, guardian_profile, student_profile, guardian_member, student_member])
    db_session.commit()
    yield
    db_session.query(StudentGuardian).delete()
    db_session.query(OrganizationMember).delete()
    db_session.query(Profile).delete()
    db_session.query(Organization).delete()
    db_session.commit()

def provide_authenticated_client(client):
    """Return a TestClient with the Authorization header set to bypass auth."""
    # In reality, you might want to use a token or mock header
    client.headers.update({"Authorization": "Bearer testtoken"})
    return client

def test_create_guardian_student_link(client: TestClient, db_session):
    client = provide_authenticated_client(client)
    link_data = {
        "guardian_id": str(mock_guardian_uuid),
        "student_id": str(mock_student_uuid),
        "relationship_type": "primary"
    }
    url = f"/api/v1/organizations/{mock_org_uuid}/guardians/link"
    response = client.post(url, json=link_data)
    assert response.status_code == 200
    data = response.json()
    assert (
        "guardian_id" in data and data["guardian_id"] == str(mock_guardian_uuid)
    ) or (
        "guardian" in data and data["guardian"]["id"] == str(mock_guardian_uuid)
    )
    assert (
        "student_id" in data and data["student_id"] == str(mock_student_uuid)
    ) or (
        "student" in data and data["student"]["id"] == str(mock_student_uuid)
    )
    assert data.get("relationship_type") == "primary" or (
        "relationship_type" in data and data["relationship_type"] == "primary"
    )
    # Verify in DB
    link = db_session.query(StudentGuardian).filter(
        StudentGuardian.organization_id == mock_org_uuid,
        StudentGuardian.guardian_id == mock_guardian_uuid,
        StudentGuardian.student_id == mock_student_uuid
    ).first()
    assert link is not None
    assert link.relationship_type == GuardianRelationType.primary

def test_get_student_guardians(client: TestClient, db_session):
    client = provide_authenticated_client(client)
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
    # Accept either key spellings
    assert (
        "guardian_id" in guardian_entry and guardian_entry["guardian_id"] == str(mock_guardian_uuid)
    ) or (
        "guardian" in guardian_entry and guardian_entry["guardian"]["id"] == str(mock_guardian_uuid)
    )

def test_get_guardian_students(client: TestClient, db_session):
    client = provide_authenticated_client(client)
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
    assert (
        "student_id" in student_entry and student_entry["student_id"] == str(mock_student_uuid)
    ) or (
        "student" in student_entry and student_entry["student"]["id"] == str(mock_student_uuid)
    )

def test_delete_guardian_student_link(client: TestClient, db_session):
    client = provide_authenticated_client(client)
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
    assert "message" in data and "removed" in data["message"].lower()
    # Verify removed from DB
    link = db_session.query(StudentGuardian).filter(
        StudentGuardian.organization_id == mock_org_uuid,
        StudentGuardian.guardian_id == mock_guardian_uuid,
        StudentGuardian.student_id == mock_student_uuid
    ).first()
    assert link is None

def test_duplicate_relationship_prevention(client: TestClient, db_session):
    client = provide_authenticated_client(client)
    link_data = {
        "guardian_id": str(mock_guardian_uuid),
        "student_id": str(mock_student_uuid),
        "relationship_type": "primary"
    }
    url = f"/api/v1/organizations/{mock_org_uuid}/guardians/link"
    response1 = client.post(url, json=link_data)
    assert response1.status_code == 200
    response2 = client.post(url, json=link_data)
    assert response2.status_code == 400
    assert "already exists" in response2.json().get("detail", "")
