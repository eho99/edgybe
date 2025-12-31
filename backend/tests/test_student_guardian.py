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
    
    # Create profile for mock_user (admin) - required for foreign key constraint
    admin_profile = Profile(
        id=mock_user.id, 
        full_name="Admin User",
        email=mock_user.email,
        phone="+14155552671",
        city="Springfield",
        state="IL",
        is_active=True
    )
    db_session.add(admin_profile)
    
    # Create admin member
    admin_member = OrganizationMember(
        organization_id=mock_org_uuid,
        user_id=mock_user.id,
        role=OrgRole.admin,
        status=MemberStatus.active
    )
    db_session.add(admin_member)
    
    # Create guardian and student profiles
    guardian_profile = Profile(
        id=mock_guardian_uuid, 
        full_name="Guardian User",
        email="guardian@example.com",
        phone="+14155552672",
        street_number="456",
        street_name="Oak Ave",
        city="Springfield",
        state="IL",
        zip_code="62702",
        is_active=True
    )
    student_profile = Profile(
        id=mock_student_uuid, 
        full_name="Student User",
        email="student@example.com",
        grade_level="9",
        student_id="STU001",
        is_active=True
    )
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


def test_get_student_guardians_with_email_via_relationship(client: TestClient, db_session):
    """Test that guardian emails are correctly retrieved via the relationship-based approach"""
    # Update guardian member to have an email
    guardian_member = db_session.query(OrganizationMember).filter(
        OrganizationMember.organization_id == mock_org_uuid,
        OrganizationMember.user_id == mock_guardian_uuid
    ).first()
    guardian_member.invite_email = "guardian@example.com"
    db_session.commit()
    
    # Create a link
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
    assert len(data["guardians"]) == 1
    
    guardian_entry = data["guardians"][0]
    # Verify email is retrieved via relationship
    assert guardian_entry["guardian_email"] == "guardian@example.com"
    assert guardian_entry["guardian_id"] == str(mock_guardian_uuid)
    assert guardian_entry["guardian"]["id"] == str(mock_guardian_uuid)
    assert guardian_entry["guardian"]["full_name"] == "Guardian User"


def test_get_student_guardians_multiple_guardians_with_emails(client: TestClient, db_session):
    """Test getting multiple guardians with different email scenarios"""
    # Create a second guardian
    second_guardian_id = uuid.uuid4()
    second_guardian_profile = Profile(
        id=second_guardian_id,
        full_name="Second Guardian",
        email="second.guardian@example.com",
        phone="+14155552673",
        city="Springfield",
        state="IL",
        is_active=True
    )
    db_session.add(second_guardian_profile)
    
    second_guardian_member = OrganizationMember(
        organization_id=mock_org_uuid,
        user_id=second_guardian_id,
        role=OrgRole.guardian,
        status=MemberStatus.active,
        invite_email="second.guardian@example.com"  # Has email
    )
    db_session.add(second_guardian_member)
    
    # Update first guardian to have email
    first_guardian_member = db_session.query(OrganizationMember).filter(
        OrganizationMember.organization_id == mock_org_uuid,
        OrganizationMember.user_id == mock_guardian_uuid
    ).first()
    first_guardian_member.invite_email = "first.guardian@example.com"
    
    # Create links for both guardians
    link1 = StudentGuardian(
        organization_id=mock_org_uuid,
        guardian_id=mock_guardian_uuid,
        student_id=mock_student_uuid,
        relationship_type=GuardianRelationType.primary
    )
    link2 = StudentGuardian(
        organization_id=mock_org_uuid,
        guardian_id=second_guardian_id,
        student_id=mock_student_uuid,
        relationship_type=GuardianRelationType.secondary
    )
    db_session.add_all([link1, link2])
    db_session.commit()

    url = f"/api/v1/organizations/{mock_org_uuid}/students/{mock_student_uuid}/guardians"
    response = client.get(url)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["guardians"]) == 2
    
    # Verify both guardians have emails retrieved via relationship
    guardian_emails = {g["guardian_email"] for g in data["guardians"]}
    print(guardian_emails)
    assert "first.guardian@example.com" in guardian_emails
    assert "second.guardian@example.com" in guardian_emails
    
    # Verify relationship types
    relationship_types = {g["relationship_type"] for g in data["guardians"]}
    assert "primary" in relationship_types
    assert "secondary" in relationship_types


def test_get_student_guardians_guardian_without_email(client: TestClient, db_session):
    """Test that guardian without email returns None for guardian_email"""
    # Ensure guardian member has no email
    guardian_member = db_session.query(OrganizationMember).filter(
        OrganizationMember.organization_id == mock_org_uuid,
        OrganizationMember.user_id == mock_guardian_uuid
    ).first()
    guardian_member.invite_email = None
    db_session.commit()
    
    # Create a link
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
    print(data)
    assert len(data["guardians"]) == 1
    
    guardian_entry = data["guardians"][0]
    # Verify email is None when not present
    assert guardian_entry["guardian_email"] is None
    assert guardian_entry["guardian_id"] == str(mock_guardian_uuid)
    assert guardian_entry["guardian"]["full_name"] == "Guardian User"


def test_get_student_guardians_nonexistent_student(client: TestClient):
    """Test that getting guardians for nonexistent student returns 404"""
    nonexistent_student_id = uuid.uuid4()
    url = f"/api/v1/organizations/{mock_org_uuid}/students/{nonexistent_student_id}/guardians"
    response = client.get(url)
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_student_guardians_no_guardians(client: TestClient):
    """Test getting guardians for student with no guardians returns empty list"""
    url = f"/api/v1/organizations/{mock_org_uuid}/students/{mock_student_uuid}/guardians"
    response = client.get(url)
    
    assert response.status_code == 200
    data = response.json()
    assert data["student"]["id"] == str(mock_student_uuid)
    assert isinstance(data["guardians"], list)
    assert len(data["guardians"]) == 0


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
    other_guardian_profile = Profile(
        id=other_guardian_id, 
        full_name="Other Guardian",
        email="other.guardian@example.com",
        phone="(555) 111-2222",
        city="Chicago",
        state="IL",
        is_active=True
    )
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
    other_student_profile = Profile(
        id=other_student_id, 
        full_name="Other Student",
        email="other.student@example.com",
        grade_level="10",
        student_id="STU002",
        is_active=True
    )
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

def test_link_guardian_with_wrong_role(client: TestClient, db_session):
    """
    Test that we cannot link a user as a 'guardian' if their org role 
    is actually 'student' or 'admin' (depending on strictness).
    """
    # Create another student in the same org
    other_student_id = uuid.uuid4()
    other_student_profile = Profile(
        id=other_student_id, 
        full_name="Other Student",
        email="other.student@example.com",
        grade_level="10",
        student_id="STU002",
        is_active=True
    )
    db_session.add(other_student_profile)
    
    # Add them to org as a STUDENT
    other_student_member = OrganizationMember(
        organization_id=mock_org_uuid,
        user_id=other_student_id,
        role=OrgRole.student, # <--- Important: They are a student
        status=MemberStatus.active
    )
    db_session.add(other_student_member)
    db_session.commit()

    link_data = {
        "guardian_id": str(other_student_id), # Trying to use a student as a guardian
        "student_id": str(mock_student_uuid),
        "relationship_type": "primary"
    }
    url = f"/api/v1/organizations/{mock_org_uuid}/guardians/link"
    response = client.post(url, json=link_data)
    
    # This asserts that your Service layer checks roles. 
    # If this fails with 200, your service is too permissive.
    assert response.status_code == 400 
    assert "role" in response.json()["detail"].lower()


def test_prevent_self_guardianship(client: TestClient):
    """Test that a student cannot be their own guardian"""
    link_data = {
        "guardian_id": str(mock_student_uuid),
        "student_id": str(mock_student_uuid),
        "relationship_type": "primary"
    }
    url = f"/api/v1/organizations/{mock_org_uuid}/guardians/link"
    response = client.post(url, json=link_data)
    
    assert response.status_code == 400
    assert "cannot be their own guardian" in response.json()["detail"].lower()


# Tests for profile creation (non-auth profiles)
def test_create_student_profile(client: TestClient, db_session):
    """Test creating a single student profile"""
    student_data = {
        "full_name": "New Student",
        "grade_level": "9",
        "student_id": "STU100",
        "email": "newstudent@example.com"
    }
    url = f"/api/v1/organizations/{mock_org_uuid}/students"
    response = client.post(url, json=student_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "New Student"
    assert data["grade_level"] == "9"
    assert data["student_id"] == "STU100"
    assert "id" in data
    
    # Verify profile exists in DB
    profile_id = uuid.UUID(data["id"])
    profile = db_session.query(Profile).filter(Profile.id == profile_id).first()
    assert profile is not None
    assert profile.full_name == "New Student"
    assert profile.grade_level == "9"
    assert profile.student_id == "STU100"
    
    # Verify organization membership exists
    member = db_session.query(OrganizationMember).filter(
        OrganizationMember.user_id == profile_id,
        OrganizationMember.organization_id == mock_org_uuid
    ).first()
    assert member is not None
    assert member.role == OrgRole.student
    assert member.status == MemberStatus.inactive


def test_create_guardian_profile(client: TestClient, db_session):
    """Test creating a single guardian profile"""
    guardian_data = {
        "full_name": "New Guardian",
        "email": "newguardian@example.com"
    }
    url = f"/api/v1/organizations/{mock_org_uuid}/guardians"
    response = client.post(url, json=guardian_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "New Guardian"
    assert "id" in data
    
    # Verify profile and membership
    profile_id = uuid.UUID(data["id"])
    profile = db_session.query(Profile).filter(Profile.id == profile_id).first()
    assert profile is not None
    
    member = db_session.query(OrganizationMember).filter(
        OrganizationMember.user_id == profile_id,
        OrganizationMember.organization_id == mock_org_uuid
    ).first()
    assert member is not None
    assert member.role == OrgRole.guardian


def test_create_guardian_profile_missing_email(client: TestClient, db_session):
    """Test that creating a guardian without email fails"""
    guardian_data = {
        "full_name": "Guardian No Email"
    }
    url = f"/api/v1/organizations/{mock_org_uuid}/guardians"
    response = client.post(url, json=guardian_data)
    assert response.status_code == 422  # Validation error


def test_create_guardian_profile_with_optional_fields(client: TestClient, db_session):
    """Test creating a guardian profile with all optional fields"""
    guardian_data = {
        "full_name": "Guardian With All Fields",
        "email": "guardian@example.com",
        "phone": "+14155555678",
        "street_number": "456",
        "street_name": "Oak Ave",
        "city": "Chicago",
        "state": "IL",
        "zip_code": "60601",
        "country": "USA",
        "preferred_language": "es"
    }
    url = f"/api/v1/organizations/{mock_org_uuid}/guardians"
    response = client.post(url, json=guardian_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Guardian With All Fields"
    assert data["phone"] == "tel:+1-415-555-5678"
    assert data["street_number"] == "456"
    assert data["street_name"] == "Oak Ave"
    assert data["city"] == "Chicago"
    assert data["state"] == "IL"
    assert data["zip_code"] == "60601"
    assert data["country"] == "USA"
    assert data["preferred_language"] == "es"


def test_create_student_profile_no_email(client: TestClient, db_session):
    """Test creating a student profile without email (email is optional for students)"""
    student_data = {
        "full_name": "Student No Email",
        "grade_level": "10",
        "student_id": "STU101"
    }
    url = f"/api/v1/organizations/{mock_org_uuid}/students"
    response = client.post(url, json=student_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Student No Email"
    assert data["grade_level"] == "10"
    assert data["student_id"] == "STU101"


def test_create_student_profile_missing_required_fields(client: TestClient, db_session):
    """Test that creating a student without required fields fails"""
    # Missing grade_level
    student_data = {
        "full_name": "Student Missing Grade",
        "student_id": "STU102"
    }
    url = f"/api/v1/organizations/{mock_org_uuid}/students"
    response = client.post(url, json=student_data)
    assert response.status_code == 422  # Validation error
    
    # Missing student_id
    student_data = {
        "full_name": "Student Missing ID",
        "grade_level": "11"
    }
    response = client.post(url, json=student_data)
    assert response.status_code == 422  # Validation error


def test_create_student_profile_with_optional_fields(client: TestClient, db_session):
    """Test creating a student profile with all optional fields"""
    student_data = {
        "full_name": "Student With All Fields",
        "grade_level": "8",
        "student_id": "STU103",
        "email": "student@example.com",
        "phone": "+14155555678",
        "street_number": "123",
        "street_name": "Main St",
        "city": "Springfield",
        "state": "IL",
        "zip_code": "62701",
        "country": "USA",
        "preferred_language": "en"
    }
    url = f"/api/v1/organizations/{mock_org_uuid}/students"
    response = client.post(url, json=student_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Student With All Fields"
    assert data["grade_level"] == "8"
    assert data["student_id"] == "STU103"
    assert data["phone"] == "tel:+1-415-555-5678"
    assert data["street_number"] == "123"
    assert data["street_name"] == "Main St"
    assert data["city"] == "Springfield"
    assert data["state"] == "IL"
    assert data["zip_code"] == "62701"
    assert data["country"] == "USA"
    assert data["preferred_language"] == "en"


def test_bulk_create_students(client: TestClient, db_session):
    """Test bulk creating student profiles"""
    students_data = {
        "students": [
            {"full_name": "Student 1", "grade_level": "9", "student_id": "STU200", "email": "s1@example.com"},
            {"full_name": "Student 2", "grade_level": "10", "student_id": "STU201", "email": "s2@example.com"},
            {"full_name": "Student 3", "grade_level": "11", "student_id": "STU202"}
        ]
    }
    url = f"/api/v1/organizations/{mock_org_uuid}/students/bulk"
    response = client.post(url, json=students_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["created"] == 3
    assert len(data["profiles"]) == 3
    
    # Verify all profiles exist
    for profile_data in data["profiles"]:
        profile_id = uuid.UUID(profile_data["id"])
        profile = db_session.query(Profile).filter(Profile.id == profile_id).first()
        assert profile is not None
        assert profile.grade_level is not None
        assert profile.student_id is not None
        member = db_session.query(OrganizationMember).filter(
            OrganizationMember.user_id == profile_id,
            OrganizationMember.organization_id == mock_org_uuid
        ).first()
        assert member is not None
        assert member.role == OrgRole.student


def test_bulk_create_guardians(client: TestClient, db_session):
    """Test bulk creating guardian profiles"""
    guardians_data = {
        "guardians": [
            {"full_name": "Guardian 1", "email": "g1@example.com"},
            {"full_name": "Guardian 2", "email": "g2@example.com"}
        ]
    }
    url = f"/api/v1/organizations/{mock_org_uuid}/guardians/bulk"
    response = client.post(url, json=guardians_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["created"] == 2
    assert len(data["profiles"]) == 2
    
    # Verify all profiles have email
    for profile_data in data["profiles"]:
        profile_id = uuid.UUID(profile_data["id"])
        profile = db_session.query(Profile).filter(Profile.id == profile_id).first()
        assert profile is not None


def test_bulk_create_and_link_pairs(client: TestClient, db_session):
    """Test bulk creating student-guardian pairs and linking them"""
    pairs_data = {
        "pairs": [
            {
                "student": {"full_name": "Student A", "grade_level": "9", "student_id": "STU300", "email": "sa@example.com"},
                "guardian": {"full_name": "Guardian A", "email": "ga@example.com"},
                "relationship_type": "primary"
            },
            {
                "student": {"full_name": "Student B", "grade_level": "10", "student_id": "STU301", "email": "sb@example.com"},
                "guardian": {"full_name": "Guardian B", "email": "gb@example.com"},
                "relationship_type": "secondary"
            }
        ]
    }
    url = f"/api/v1/organizations/{mock_org_uuid}/pairs/bulk"
    response = client.post(url, json=pairs_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["created"] == 2
    assert len(data["pairs"]) == 2
    
    # Verify first pair
    pair1 = data["pairs"][0]
    assert pair1["student_profile"]["full_name"] == "Student A"
    assert pair1["guardian_profile"]["full_name"] == "Guardian A"
    assert pair1["link"] is not None
    assert pair1["link"]["relationship_type"] == "primary"
    
    # Verify second pair
    pair2 = data["pairs"][1]
    assert pair2["link"]["relationship_type"] == "secondary"
    
    # Verify links exist in DB
    for pair in data["pairs"]:
        student_id = uuid.UUID(pair["student_profile"]["id"])
        guardian_id = uuid.UUID(pair["guardian_profile"]["id"])
        link = db_session.query(StudentGuardian).filter(
            StudentGuardian.student_id == student_id,
            StudentGuardian.guardian_id == guardian_id
        ).first()
        assert link is not None


def test_create_student_then_link(client: TestClient, db_session):
    """Test creating student and guardian separately, then linking"""
    # Create student
    student_data = {
        "full_name": "Test Student",
        "grade_level": "12",
        "student_id": "STU400"
    }
    student_url = f"/api/v1/organizations/{mock_org_uuid}/students"
    student_response = client.post(student_url, json=student_data)
    assert student_response.status_code == 200
    student_id = student_response.json()["id"]
    
    # Create guardian
    guardian_data = {
        "full_name": "Test Guardian",
        "email": "testguardian@example.com"
    }
    guardian_url = f"/api/v1/organizations/{mock_org_uuid}/guardians"
    guardian_response = client.post(guardian_url, json=guardian_data)
    assert guardian_response.status_code == 200
    guardian_id = guardian_response.json()["id"]
    
    # Link them
    link_data = {
        "student_id": student_id,
        "guardian_id": guardian_id,
        "relationship_type": "primary"
    }
    link_url = f"/api/v1/organizations/{mock_org_uuid}/guardians/link"
    link_response = client.post(link_url, json=link_data)
    
    assert link_response.status_code == 200
    link_data_response = link_response.json()
    assert link_data_response["student_id"] == student_id
    assert link_data_response["guardian_id"] == guardian_id


def test_duplicate_profile_prevention(client: TestClient, db_session):
    """Test that creating a profile with existing ID fails"""
    # Create a profile manually
    existing_id = uuid.uuid4()
    existing_profile = Profile(
        id=existing_id, 
        full_name="Existing",
        email="existing@example.com",
        grade_level="11",
        student_id="STU003",
        is_active=True
    )
    db_session.add(existing_profile)
    db_session.commit()
    
    # Try to create with same ID
    student_data = {"full_name": "Existing", "grade_level": "11", "student_id": "STU003"}
    url = f"/api/v1/organizations/{mock_org_uuid}/students"
    response = client.post(url, json=student_data)
    assert response.status_code == 400
    assert "already exists" in response.json().get("detail", "").lower()


def test_bulk_create_with_some_failures(client: TestClient, db_session):
    """Test that bulk operations handle partial failures gracefully"""
    # This test would require more complex setup to force failures
    # For now, just verify bulk operations work with valid data
    students_data = {
        "students": [
            {"full_name": "Valid Student 1", "grade_level": "9", "student_id": "STU500"},
            {"full_name": "Valid Student 2", "grade_level": "10", "student_id": "STU501"}
        ]
    }
    url = f"/api/v1/organizations/{mock_org_uuid}/students/bulk"
    response = client.post(url, json=students_data)
    
    assert response.status_code == 200
    assert response.json()["created"] == 2


def test_duplicate_student_id_prevention(client: TestClient, db_session):
    """Test that duplicate student_id values are prevented"""
    student_data = {
        "full_name": "First Student",
        "grade_level": "9",
        "student_id": "STU600"
    }
    url = f"/api/v1/organizations/{mock_org_uuid}/students"
    
    # Create first student
    response1 = client.post(url, json=student_data)
    assert response1.status_code == 200
    
    # Try to create another student with same student_id
    student_data["full_name"] = "Second Student"
    response2 = client.post(url, json=student_data)
    assert response2.status_code == 400
    assert "student_id" in response2.json()["detail"].lower()


def test_list_students_endpoint(client: TestClient):
    """Test listing students without search"""
    url = f"/api/v1/organizations/{mock_org_uuid}/students"
    response = client.get(url)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["profiles"]) >= 1


def test_list_students_with_search_by_name(client: TestClient, db_session):
    """Test searching students by name"""
    # Create additional student with specific name
    search_student_id = uuid.uuid4()
    search_student_profile = Profile(
        id=search_student_id,
        full_name="John Searchable",
        email="john.searchable@example.com",
        grade_level="10",
        student_id="STU_SEARCH_001",
        is_active=True
    )
    db_session.add(search_student_profile)
    
    search_student_member = OrganizationMember(
        organization_id=mock_org_uuid,
        user_id=search_student_id,
        role=OrgRole.student,
        status=MemberStatus.active
    )
    db_session.add(search_student_member)
    db_session.commit()
    
    # Search by name
    url = f"/api/v1/organizations/{mock_org_uuid}/students?search=Searchable"
    response = client.get(url)
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    # Should find our searchable student
    found_student = any(p["id"] == str(search_student_id) for p in data["profiles"])
    assert found_student, f"Expected to find student {search_student_id} in search results"


def test_list_students_with_search_by_student_id(client: TestClient, db_session):
    """Test searching students by student_id"""
    # Create additional student with specific student_id
    search_student_id = uuid.uuid4()
    search_student_profile = Profile(
        id=search_student_id,
        full_name="Test Student",
        email="test.student@example.com",
        grade_level="11",
        student_id="STU_SEARCH_002",
        is_active=True
    )
    db_session.add(search_student_profile)
    
    search_student_member = OrganizationMember(
        organization_id=mock_org_uuid,
        user_id=search_student_id,
        role=OrgRole.student,
        status=MemberStatus.active
    )
    db_session.add(search_student_member)
    db_session.commit()
    
    # Search by student_id
    url = f"/api/v1/organizations/{mock_org_uuid}/students?search=STU_SEARCH_002"
    response = client.get(url)
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    # Should find our searchable student
    found_student = any(p["id"] == str(search_student_id) for p in data["profiles"])
    assert found_student, f"Expected to find student {search_student_id} in search results"
    # Verify the student_id matches
    student = next(p for p in data["profiles"] if p["id"] == str(search_student_id))
    assert student["student_id"] == "STU_SEARCH_002"


def test_list_students_search_case_insensitive(client: TestClient, db_session):
    """Test that search is case-insensitive"""
    # Create student with mixed case name
    search_student_id = uuid.uuid4()
    search_student_profile = Profile(
        id=search_student_id,
        full_name="Jane Doe",
        email="jane.doe@example.com",
        grade_level="9",
        student_id="STU_CASE_001",
        is_active=True
    )
    db_session.add(search_student_profile)
    
    search_student_member = OrganizationMember(
        organization_id=mock_org_uuid,
        user_id=search_student_id,
        role=OrgRole.student,
        status=MemberStatus.active
    )
    db_session.add(search_student_member)
    db_session.commit()
    
    # Search with lowercase
    url = f"/api/v1/organizations/{mock_org_uuid}/students?search=jane"
    response = client.get(url)
    
    assert response.status_code == 200
    data = response.json()
    found_student = any(p["id"] == str(search_student_id) for p in data["profiles"])
    assert found_student, "Case-insensitive search should find 'Jane Doe' when searching 'jane'"


def test_list_students_search_partial_match(client: TestClient, db_session):
    """Test that search supports partial matching"""
    # Create student
    search_student_id = uuid.uuid4()
    search_student_profile = Profile(
        id=search_student_id,
        full_name="Alice Smith",
        email="alice.smith@example.com",
        grade_level="8",
        student_id="STU_PARTIAL_001",
        is_active=True
    )
    db_session.add(search_student_profile)
    
    search_student_member = OrganizationMember(
        organization_id=mock_org_uuid,
        user_id=search_student_id,
        role=OrgRole.student,
        status=MemberStatus.active
    )
    db_session.add(search_student_member)
    db_session.commit()
    
    # Search with partial name
    url = f"/api/v1/organizations/{mock_org_uuid}/students?search=lice"
    response = client.get(url)
    
    assert response.status_code == 200
    data = response.json()
    found_student = any(p["id"] == str(search_student_id) for p in data["profiles"])
    assert found_student, "Partial search should find 'Alice Smith' when searching 'lice'"


def test_list_students_search_no_results(client: TestClient):
    """Test search with no matching results"""
    url = f"/api/v1/organizations/{mock_org_uuid}/students?search=NonexistentStudent12345"
    response = client.get(url)
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["profiles"]) == 0


def test_list_students_search_with_pagination(client: TestClient, db_session):
    """Test search with pagination"""
    # Create multiple students with searchable names
    student_ids = []
    for i in range(5):
        student_id = uuid.uuid4()
        student_profile = Profile(
            id=student_id,
            full_name=f"Searchable Student {i}",
            email=f"student{i}@example.com",
            grade_level="9",
            student_id=f"STU_PAGE_{i:03d}",
            is_active=True
        )
        db_session.add(student_profile)
        
        student_member = OrganizationMember(
            organization_id=mock_org_uuid,
            user_id=student_id,
            role=OrgRole.student,
            status=MemberStatus.active
        )
        db_session.add(student_member)
        student_ids.append(student_id)
    
    db_session.commit()
    
    # Search and get first page
    url = f"/api/v1/organizations/{mock_org_uuid}/students?search=Searchable&page=1&per_page=2"
    response = client.get(url)
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 5  # At least our 5 students
    assert len(data["profiles"]) == 2  # Per page limit
    assert data["page"] == 1
    assert data["per_page"] == 2
    assert data["total_pages"] >= 3  # At least 3 pages with 2 per page


def test_list_students_staff_can_access(client: TestClient, db_session):
    """Test that staff members can access the students endpoint"""
    # Create a staff member
    staff_user_id = uuid.uuid4()
    staff_profile = Profile(
        id=staff_user_id,
        full_name="Staff User",
        email="staff@example.com",
        is_active=True
    )
    db_session.add(staff_profile)
    
    staff_member = OrganizationMember(
        organization_id=mock_org_uuid,
        user_id=staff_user_id,
        role=OrgRole.staff,
        status=MemberStatus.active
    )
    db_session.add(staff_member)
    db_session.commit()
    
    # Override auth to return staff member
    from app.main import app
    from app.auth import get_current_active_member, require_active_role
    from app import schemas
    from fastapi import Request
    
    async def override_get_current_active_member_staff(
        request: Request,
        org_id,
        db,
        user
    ):
        return schemas.AuthenticatedMember(
            user=schemas.SupabaseUser(id=staff_user_id, email="staff@example.com"),
            org_id=mock_org_uuid,
            role=OrgRole.staff
        )
    
    app.dependency_overrides[get_current_active_member] = override_get_current_active_member_staff
    app.dependency_overrides[require_active_role] = override_get_current_active_member_staff
    
    try:
        url = f"/api/v1/organizations/{mock_org_uuid}/students"
        response = client.get(url)
        
        assert response.status_code == 200
        data = response.json()
        assert "profiles" in data
    finally:
        # Clean up overrides
        app.dependency_overrides.clear()


def test_update_student_profile(client: TestClient, db_session):
    url = f"/api/v1/organizations/{mock_org_uuid}/students/{mock_student_uuid}"
    payload = {
        "full_name": "Updated Student",
        "phone": "+14155550000",
        "city": "Updated City"
    }
    response = client.patch(url, json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Student"
    assert data["phone"] == "tel:+1-415-555-0000"
    assert data["city"] == "Updated City"


def test_update_guardian_profile(client: TestClient, db_session):
    url = f"/api/v1/organizations/{mock_org_uuid}/guardians/{mock_guardian_uuid}"
    payload = {
        "full_name": "Updated Guardian",
        "phone": "+14155550001",
        "country": "USA"
    }
    response = client.patch(url, json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Guardian"
    assert data["phone"] == "tel:+1-415-555-0001"
    assert data["country"] == "USA"


def test_archive_student_profile(client: TestClient, db_session):
    """Admin can archive a student profile."""
    url = f"/api/v1/organizations/{mock_org_uuid}/students/{mock_student_uuid}"
    response = client.delete(url)

    assert response.status_code == 200
    assert "archived" in response.json().get("message", "").lower()

    profile = db_session.query(Profile).filter(Profile.id == mock_student_uuid).first()
    assert profile is not None
    assert profile.is_active is False

    member = db_session.query(OrganizationMember).filter(
        OrganizationMember.organization_id == mock_org_uuid,
        OrganizationMember.user_id == mock_student_uuid,
        OrganizationMember.role == OrgRole.student
    ).first()
    assert member is not None
    assert member.status == MemberStatus.inactive

    list_response = client.get(f"/api/v1/organizations/{mock_org_uuid}/students")
    assert list_response.status_code == 200
    assert all(p["id"] != str(mock_student_uuid) for p in list_response.json()["profiles"])


def test_archive_guardian_profile(client: TestClient, db_session):
    """Admin can archive a guardian profile."""
    url = f"/api/v1/organizations/{mock_org_uuid}/guardians/{mock_guardian_uuid}"
    response = client.delete(url)

    assert response.status_code == 200
    assert "archived" in response.json().get("message", "").lower()

    profile = db_session.query(Profile).filter(Profile.id == mock_guardian_uuid).first()
    assert profile is not None
    assert profile.is_active is False

    member = db_session.query(OrganizationMember).filter(
        OrganizationMember.organization_id == mock_org_uuid,
        OrganizationMember.user_id == mock_guardian_uuid,
        OrganizationMember.role == OrgRole.guardian
    ).first()
    assert member is not None
    assert member.status == MemberStatus.inactive

    list_response = client.get(f"/api/v1/organizations/{mock_org_uuid}/guardians")
    assert list_response.status_code == 200
    assert all(p["id"] != str(mock_guardian_uuid) for p in list_response.json()["profiles"])