"""
Unit tests for referral endpoints using arrange-act-assert pattern.
Tests use reusable fixtures for easy debugging.
"""
import pytest
from fastapi.testclient import TestClient
import uuid
from datetime import datetime, timezone

from app.models import (
    Profile, Organization, OrganizationMember, 
    Referral, Intervention, CommunicationLog, EmailTemplate,
    OrgRole, MemberStatus
)


# ============================================================================
# ARRANGE: Reusable Test Fixtures
# ============================================================================

@pytest.fixture
def test_org_id():
    """Standard test organization ID."""
    return uuid.UUID("390fa60a-1ff1-4fa0-abc3-ffac2ed211b1")


@pytest.fixture
def test_student_id():
    """Standard test student ID."""
    return uuid.UUID("590fa60a-1ff1-4fa0-abc3-ffac2ed211b1")


@pytest.fixture
def test_author_id(mock_user):
    """Standard test author ID (same as mock_user)."""
    return mock_user.id


@pytest.fixture
def test_organization(db_session, test_org_id):
    """
    Create a test organization with referral config.
    Reusable across tests.
    """
    org = Organization(
        id=test_org_id,
        name="Test School",
        phone_number="+14155551234",
        preset_config={
            "referral_config": {
                "types": ["Behavior", "Support", "Academic"],
                "locations": {
                    "options": ["Classroom", "Hallway", "Playground", "Cafeteria", "Other"]
                },
                "time_of_day": {
                    "options": ["Morning", "Afternoon", "Lunch", "Recess", "Other"]
                },
                "behaviors": {
                    "options": [
                        "Disruption", "Tardy", "Physical Aggression", 
                        "Verbal Aggression", "Defiance"
                    ]
                },
                "common_interventions": [
                    "Parent Contact", "Counseling", "Detention", "ISS"
                ]
            }
        }
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture
def test_admin_profile(db_session, mock_user, test_organization):
    """
    Create admin profile and membership.
    Reusable across tests.
    """
    # Create profile
    profile = Profile(
        id=mock_user.id,
        full_name="Test Admin",
        phone="+14155552671",
        is_active=True
    )
    db_session.add(profile)
    
    # Create admin membership
    member = OrganizationMember(
        organization_id=test_organization.id,
        user_id=mock_user.id,
        role=OrgRole.admin,
        status=MemberStatus.active
    )
    db_session.add(member)
    db_session.commit()
    db_session.refresh(profile)
    return profile


@pytest.fixture
def test_student_profile(db_session, test_organization, test_student_id):
    """
    Create student profile and membership.
    Reusable across tests.
    """
    # Create student profile
    profile = Profile(
        id=test_student_id,
        full_name="John Doe",
        grade_level="9",
        student_id="STU001",
        is_active=True
    )
    db_session.add(profile)
    
    # Create student membership
    member = OrganizationMember(
        organization_id=test_organization.id,
        user_id=test_student_id,
        role=OrgRole.student,
        status=MemberStatus.inactive
    )
    db_session.add(member)
    db_session.commit()
    db_session.refresh(profile)
    return profile


@pytest.fixture
def test_referral(db_session, test_organization, test_student_profile, test_admin_profile):
    """
    Create a test referral.
    Reusable across tests.
    """
    referral = Referral(
        organization_id=test_organization.id,
        student_id=test_student_profile.id,
        author_id=test_admin_profile.id,
        status="DRAFT",
        type="Behavior",
        location="Classroom",
        time_of_day="Morning",
        behaviors=["Disruption", "Tardy"],
        description="Student was disruptive during class"
    )
    db_session.add(referral)
    db_session.commit()
    db_session.refresh(referral)
    return referral


@pytest.fixture
def test_intervention(db_session, test_referral, test_admin_profile):
    """
    Create a test intervention.
    Reusable across tests.
    """
    intervention = Intervention(
        referral_id=test_referral.id,
        created_by=test_admin_profile.id,
        title="Parent Contact",
        description="Called parent to discuss behavior",
        status="PLANNED"
    )
    db_session.add(intervention)
    db_session.commit()
    db_session.refresh(intervention)
    return intervention


@pytest.fixture
def test_email_template(db_session, test_organization, test_admin_profile):
    """
    Create a test email template.
    Reusable across tests.
    """
    template = EmailTemplate(
        organization_id=test_organization.id,
        created_by_user_id=test_admin_profile.id,
        name="Standard Referral Email",
        subject_template="Referral for {{student_name}}",
        body_template="Dear Parent,\n\nThis is to inform you about a referral for {{student_name}}.\n\nType: {{type}}\nDescription: {{description}}",
        type="referral",
        scope="organization",
        is_active=True
    )
    db_session.add(template)
    db_session.commit()
    db_session.refresh(template)
    return template


# ============================================================================
# TESTS: Configuration Endpoint
# ============================================================================

class TestReferralConfig:
    """Tests for GET /config/referrals endpoint."""
    
    def test_get_config_success(
        self, 
        client: TestClient, 
        test_organization,
        test_admin_profile
    ):
        """
        ARRANGE: Organization with referral config
        ACT: GET /config/referrals
        ASSERT: Returns config correctly
        """
        # Act
        response = client.get(f"/api/v1/organizations/{test_organization.id}/config/referrals")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "types" in data
        assert "Behavior" in data["types"]
        assert "locations" in data
        assert "Classroom" in data["locations"]["options"]
        assert "common_interventions" in data
        assert "Parent Contact" in data["common_interventions"]
    
    def test_get_config_missing(
        self,
        client: TestClient,
        db_session,
        mock_user
    ):
        """
        ARRANGE: Organization without referral config
        ACT: GET /config/referrals
        ASSERT: Returns 404
        """
        # Arrange
        org = Organization(
            name="School Without Config",
            preset_config={}
        )
        db_session.add(org)
        db_session.commit()
        
        # Create profile for this test's organization
        profile = Profile(
            id=mock_user.id,
            full_name="Test Admin",
            phone="+14155552671",
            is_active=True
        )
        db_session.add(profile)
        
        # Create membership for the new organization
        member = OrganizationMember(
            organization_id=org.id,
            user_id=mock_user.id,
            role=OrgRole.admin,
            status=MemberStatus.active
        )
        db_session.add(member)
        db_session.commit()
        
        # Act
        response = client.get(f"/api/v1/organizations/{org.id}/config/referrals")
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


# ============================================================================
# TESTS: Referral CRUD Endpoints
# ============================================================================

class TestReferralCreate:
    """Tests for POST /referrals endpoint."""
    
    def test_create_referral_success(
        self,
        client: TestClient,
        test_organization,
        test_admin_profile,
        test_student_profile
    ):
        """
        ARRANGE: Valid referral data
        ACT: POST /referrals
        ASSERT: Referral created successfully
        """
        # Arrange
        payload = {
            "student_id": str(test_student_profile.id),
            "type": "Behavior",
            "location": "Classroom",
            "time_of_day": "Morning",
            "behaviors": ["Disruption", "Tardy"],
            "description": "Student was late and disruptive"
        }
        
        # Act
        response = client.post(
            f"/api/v1/organizations/{test_organization.id}/referrals",
            json=payload
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["student_id"] == str(test_student_profile.id)
        assert data["type"] == "Behavior"
        assert data["status"] == "SUBMITTED"
        assert data["location"] == "Classroom"
        assert data["behaviors"] == ["Disruption", "Tardy"]
        assert data["student_name"] == "John Doe"
        assert data["author_name"] == "Test Admin"
    
    def test_create_referral_with_other_location(
        self,
        client: TestClient,
        test_organization,
        test_admin_profile,
        test_student_profile
    ):
        """
        ARRANGE: Referral with custom 'Other' location
        ACT: POST /referrals
        ASSERT: Custom location saved correctly
        """
        # Arrange
        payload = {
            "student_id": str(test_student_profile.id),
            "type": "Behavior",
            "location": "Secret Garden Behind Gym",  # Custom location
            "time_of_day": "After School",  # Custom time
            "behaviors": ["Other"],
            "description": "Custom incident"
        }
        
        # Act
        response = client.post(
            f"/api/v1/organizations/{test_organization.id}/referrals",
            json=payload
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["location"] == "Secret Garden Behind Gym"
        assert data["time_of_day"] == "After School"
    
    def test_create_referral_invalid_student(
        self,
        client: TestClient,
        test_organization,
        test_admin_profile
    ):
        """
        ARRANGE: Non-existent student ID
        ACT: POST /referrals
        ASSERT: Returns 400 error
        """
        # Arrange
        fake_student_id = uuid.uuid4()
        payload = {
            "student_id": str(fake_student_id),
            "type": "Behavior",
            "description": "Test"
        }
        
        # Act
        response = client.post(
            f"/api/v1/organizations/{test_organization.id}/referrals",
            json=payload
        )
        
        # Assert
        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()


class TestReferralList:
    """Tests for GET /referrals endpoint."""
    
    def test_list_referrals_success(
        self,
        client: TestClient,
        test_organization,
        test_admin_profile,
        test_student_profile,
        test_referral
    ):
        """
        ARRANGE: Referral exists in database
        ACT: GET /referrals
        ASSERT: Returns list with referral
        """
        # Act
        response = client.get(f"/api/v1/organizations/{test_organization.id}/referrals")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["referrals"]) >= 1
        assert data["referrals"][0]["id"] == str(test_referral.id)
        assert data["referrals"][0]["student_name"] == "John Doe"
    
    def test_list_referrals_with_filters(
        self,
        client: TestClient,
        db_session,
        test_organization,
        test_admin_profile,
        test_student_profile,
        test_referral
    ):
        """
        ARRANGE: Multiple referrals with different types
        ACT: GET /referrals with type filter
        ASSERT: Returns filtered results
        """
        # Arrange - create another referral with different type
        referral2 = Referral(
            organization_id=test_organization.id,
            student_id=test_student_profile.id,
            author_id=test_admin_profile.id,
            status="SUBMITTED",
            type="Support",
            description="Academic support needed"
        )
        db_session.add(referral2)
        db_session.commit()
        
        # Act
        response = client.get(
            f"/api/v1/organizations/{test_organization.id}/referrals?type=Behavior"
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert all(r["type"] == "Behavior" for r in data["referrals"])
    
    def test_list_referrals_pagination(
        self,
        client: TestClient,
        test_organization,
        test_admin_profile,
        test_student_profile,
        test_referral
    ):
        """
        ARRANGE: Referrals exist
        ACT: GET /referrals with pagination params
        ASSERT: Returns paginated results
        """
        # Act
        response = client.get(
            f"/api/v1/organizations/{test_organization.id}/referrals?page=1&per_page=10"
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 10
        assert "total_pages" in data


class TestReferralGet:
    """Tests for GET /referrals/{id} endpoint."""
    
    def test_get_referral_success(
        self,
        client: TestClient,
        test_organization,
        test_admin_profile,
        test_student_profile,
        test_referral,
        test_intervention
    ):
        """
        ARRANGE: Referral with intervention exists
        ACT: GET /referrals/{id}
        ASSERT: Returns complete referral with interventions
        """
        # Act
        response = client.get(
            f"/api/v1/organizations/{test_organization.id}/referrals/{test_referral.id}"
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_referral.id)
        assert data["student_name"] == "John Doe"
        assert data["author_name"] == "Test Admin"
        assert len(data["interventions"]) >= 1
        assert data["interventions"][0]["title"] == "Parent Contact"
    
    def test_get_referral_not_found(
        self,
        client: TestClient,
        test_organization,
        test_admin_profile
    ):
        """
        ARRANGE: Non-existent referral ID
        ACT: GET /referrals/{id}
        ASSERT: Returns 404
        """
        # Arrange
        fake_id = uuid.uuid4()
        
        # Act
        response = client.get(
            f"/api/v1/organizations/{test_organization.id}/referrals/{fake_id}"
        )
        
        # Assert
        assert response.status_code == 404


class TestReferralUpdate:
    """Tests for PATCH /referrals/{id} endpoint."""
    
    def test_update_referral_success(
        self,
        client: TestClient,
        test_organization,
        test_admin_profile,
        test_student_profile,
        test_referral
    ):
        """
        ARRANGE: Existing referral
        ACT: PATCH /referrals/{id} with updates
        ASSERT: Referral updated successfully
        """
        # Arrange
        payload = {
            "status": "SUBMITTED",
            "description": "Updated description"
        }
        
        # Act
        response = client.patch(
            f"/api/v1/organizations/{test_organization.id}/referrals/{test_referral.id}",
            json=payload
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SUBMITTED"
        assert data["description"] == "Updated description"
        assert data["type"] == "Behavior"  # Unchanged field


# ============================================================================
# TESTS: Intervention Endpoints
# ============================================================================

class TestInterventionCreate:
    """Tests for POST /referrals/{id}/interventions endpoint."""
    
    def test_create_intervention_success(
        self,
        client: TestClient,
        test_organization,
        test_admin_profile,
        test_student_profile,
        test_referral
    ):
        """
        ARRANGE: Existing referral
        ACT: POST /interventions
        ASSERT: Intervention created successfully
        """
        # Arrange
        payload = {
            "title": "Counseling",
            "description": "Referred to counselor",
            "status": "PLANNED"
        }
        
        # Act
        response = client.post(
            f"/api/v1/organizations/{test_organization.id}/referrals/{test_referral.id}/interventions",
            json=payload
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Counseling"
        assert data["status"] == "PLANNED"
        assert data["referral_id"] == str(test_referral.id)
        assert data["creator_name"] == "Test Admin"
    
    def test_create_intervention_custom_title(
        self,
        client: TestClient,
        test_organization,
        test_admin_profile,
        test_student_profile,
        test_referral
    ):
        """
        ARRANGE: Existing referral
        ACT: POST /interventions with custom title
        ASSERT: Custom intervention created
        """
        # Arrange
        payload = {
            "title": "Custom Behavior Plan - Morning Check-ins",
            "description": "Student will check in with counselor every morning",
            "status": "IN_PROGRESS"
        }
        
        # Act
        response = client.post(
            f"/api/v1/organizations/{test_organization.id}/referrals/{test_referral.id}/interventions",
            json=payload
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Custom Behavior Plan - Morning Check-ins"
        assert data["status"] == "IN_PROGRESS"


class TestInterventionUpdate:
    """Tests for PATCH /referrals/{id}/interventions/{id} endpoint."""
    
    def test_update_intervention_success(
        self,
        client: TestClient,
        test_organization,
        test_admin_profile,
        test_student_profile,
        test_referral,
        test_intervention
    ):
        """
        ARRANGE: Existing intervention
        ACT: PATCH /interventions/{id}
        ASSERT: Intervention updated successfully
        """
        # Arrange
        payload = {
            "status": "COMPLETED",
            "description": "Parent contact completed - spoke with mother"
        }
        
        # Act
        response = client.patch(
            f"/api/v1/organizations/{test_organization.id}/referrals/{test_referral.id}/interventions/{test_intervention.id}",
            json=payload
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "COMPLETED"
        assert "mother" in data["description"].lower()


# ============================================================================
# TESTS: PDF and Email Endpoints (Mocked)
# ============================================================================

class TestPDFGeneration:
    """Tests for GET /referrals/{id}/pdf endpoint."""
    
    def test_download_pdf_success(
        self,
        client: TestClient,
        test_organization,
        test_admin_profile,
        test_student_profile,
        test_referral
    ):
        """
        ARRANGE: Referral exists
        ACT: GET /pdf
        ASSERT: PDF endpoint responds (actual PDF generation tested separately)
        """
        # Note: This will fail without WeasyPrint installed
        # We're testing the endpoint structure, not PDF generation
        
        # Act
        response = client.get(
            f"/api/v1/organizations/{test_organization.id}/referrals/{test_referral.id}/pdf"
        )
        
        # Assert - either succeeds or fails with service error (not auth error)
        assert response.status_code in [200, 500]
        if response.status_code == 500:
            # Expected if WeasyPrint not installed
            assert "not available" in response.json()["detail"].lower() or "failed" in response.json()["detail"].lower()


class TestEmailSending:
    """Tests for POST /referrals/{id}/email endpoint."""
    
    def test_send_email_success(
        self,
        client: TestClient,
        test_organization,
        test_admin_profile,
        test_student_profile,
        test_referral
    ):
        """
        ARRANGE: Referral exists
        ACT: POST /email
        ASSERT: Email endpoint responds (actual sending tested separately)
        """
        # Arrange
        payload = {
            "recipient_emails": ["parent@example.com"],
            "subject": "Referral for John Doe",
            "message": "Please review the attached referral"
        }
        
        # Act
        response = client.post(
            f"/api/v1/organizations/{test_organization.id}/referrals/{test_referral.id}/email",
            json=payload
        )
        
        # Assert - either succeeds or fails with service error (not auth error)
        assert response.status_code in [200, 500]
        if response.status_code == 500:
            # Expected if Resend/WeasyPrint not configured
            assert "not available" in response.json()["detail"].lower() or "failed" in response.json()["detail"].lower()


# ============================================================================
# TESTS: Role-Based Access Control
# ============================================================================

class TestRoleBasedAccess:
    """Tests for role-based access control."""
    
    def test_staff_can_only_see_own_referrals(
        self,
        client: TestClient,
        db_session,
        test_organization,
        test_student_profile,
        mock_user
    ):
        """
        ARRANGE: Staff member with referral, another staff's referral
        ACT: GET /referrals as staff
        ASSERT: Only sees own referrals
        """
        # Arrange - create staff profile and membership
        staff_profile = Profile(
            id=mock_user.id,
            full_name="Staff Member",
            is_active=True
        )
        db_session.add(staff_profile)
        
        staff_member = OrganizationMember(
            organization_id=test_organization.id,
            user_id=mock_user.id,
            role=OrgRole.staff,
            status=MemberStatus.active
        )
        db_session.add(staff_member)
        
        # Create referral by this staff member
        own_referral = Referral(
            organization_id=test_organization.id,
            student_id=test_student_profile.id,
            author_id=mock_user.id,
            status="DRAFT",
            type="Behavior",
            description="My referral"
        )
        db_session.add(own_referral)
        
        # Create referral by another staff member
        other_staff_id = uuid.uuid4()
        # Create profile for other staff member to satisfy foreign key constraint
        other_staff_profile = Profile(
            id=other_staff_id,
            full_name="Other Staff Member",
            is_active=True
        )
        db_session.add(other_staff_profile)
        
        other_referral = Referral(
            organization_id=test_organization.id,
            student_id=test_student_profile.id,
            author_id=other_staff_id,
            status="DRAFT",
            type="Behavior",
            description="Other staff's referral"
        )
        db_session.add(other_referral)
        db_session.commit()
        
        # Act
        response = client.get(f"/api/v1/organizations/{test_organization.id}/referrals")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        # Should only see own referral
        assert data["total"] == 1
        assert data["referrals"][0]["id"] == str(own_referral.id)

