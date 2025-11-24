import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from uuid import uuid4

from app.models import OrganizationMember, Profile, MemberStatus, OrgRole, Organization


@pytest.fixture
def test_org(db_session, mock_user):
    """Create a test organization with admin member."""
    org = Organization(id=uuid4(), name="Test Organization")
    db_session.add(org)
    
    # Create admin member for the mock_user
    admin_member = OrganizationMember(
        organization_id=org.id,
        user_id=mock_user.id,
        role=OrgRole.admin,
        status=MemberStatus.active
    )
    db_session.add(admin_member)
    
    # Create admin profile
    admin_profile = Profile(
        id=mock_user.id,
        full_name="Admin User",
        email=mock_user.email,
        has_completed_profile=True,
        phone="(555) 123-4567",
        city="Springfield",
        state="IL",
        is_active=True
    )
    db_session.add(admin_profile)
    
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture
def sample_member(db_session, test_org):
    """Create a sample member in the organization."""
    user_id = uuid4()
    email = f"user-{user_id.hex[:8]}@example.com"
    profile = Profile(
        id=user_id,
        full_name="Test User",
        email=email,
        has_completed_profile=True,
        phone="(555) 234-5678",
        city="Springfield",
        state="IL",
        is_active=True
    )
    db_session.add(profile)
    
    member = OrganizationMember(
        id=uuid4(),
        organization_id=test_org.id,
        user_id=user_id,
        role=OrgRole.staff,
        status=MemberStatus.active,
        joined_at=datetime.utcnow()
    )
    db_session.add(member)
    db_session.commit()
    db_session.refresh(member)
    # Store email for easy access in tests
    member.profile_email = email
    return member


@pytest.fixture
def sample_inactive_member(db_session, test_org):
    """Create a sample inactive member (staff role, not student/guardian)."""
    user_id = uuid4()
    email = f"inactive-{user_id.hex[:8]}@example.com"
    profile = Profile(
        id=user_id,
        full_name="Inactive User",
        email=email,
        has_completed_profile=True,
        phone="(555) 345-6789",
        city="Springfield",
        state="IL",
        is_active=False
    )
    db_session.add(profile)
    
    member = OrganizationMember(
        id=uuid4(),
        organization_id=test_org.id,
        user_id=user_id,
        role=OrgRole.staff,  # Use staff role, not student (students/guardians are filtered out)
        status=MemberStatus.active,
        joined_at=datetime.utcnow()
    )
    db_session.add(member)
    db_session.commit()
    db_session.refresh(member)
    member.profile_email = email
    return member


class TestAccountManagementEndpoints:
    
    def test_list_accounts_success(self, client: TestClient, test_org, sample_member):
        """Test successful listing of accounts"""
        response = client.get(f"/api/v1/organizations/{test_org.id}/members")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1  # At least the sample member
        assert len(data["accounts"]) >= 1
        # Find our sample member in the results
        member_accounts = [acc for acc in data["accounts"] if acc["id"] == str(sample_member.id)]
        assert len(member_accounts) == 1
        assert member_accounts[0]["role"] == "staff"
        assert member_accounts[0]["status"] == "active"
        assert member_accounts[0]["email"] == sample_member.profile_email
        assert data["page"] == 1
        assert data["per_page"] == 10
    
    def test_list_accounts_with_filters(self, client: TestClient, test_org, sample_member):
        """Test listing accounts with status filter and search"""
        # Test with status filter
        response = client.get(
            f"/api/v1/organizations/{test_org.id}/members",
            params={"status_filter": "active"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert all(acc["status"] == "active" for acc in data["accounts"])
        
        # Test with search
        response = client.get(
            f"/api/v1/organizations/{test_org.id}/members",
            params={"search": "Test User"}
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should find our sample member
        assert any(acc["id"] == str(sample_member.id) for acc in data["accounts"])
    
    def test_list_accounts_includes_inactive(self, client: TestClient, test_org, sample_inactive_member, mock_user, db_session):
        """Test listing accounts includes inactive members"""
        # Verify the inactive member exists in the database
        db_member = db_session.query(OrganizationMember).filter(
            OrganizationMember.id == sample_inactive_member.id
        ).first()
        assert db_member is not None, "Inactive member should exist in database"
        assert db_member.status == MemberStatus.active, "Fixture should create active member before status update"
        assert db_member.role == OrgRole.staff, "Member should be staff role"
        
        # Manually set the member to inactive for the test scenario
        db_member.status = MemberStatus.inactive
        db_session.commit()
        
        response = client.get(f"/api/v1/organizations/{test_org.id}/members")
        
        assert response.status_code == 200
        data = response.json()
        # Should include inactive members by default (no status filter)
        # Check that our specific inactive member is in the results
        inactive_accounts = [acc for acc in data["accounts"] if acc["status"] == "inactive"]
        member_found = any(acc["id"] == str(sample_inactive_member.id) for acc in data["accounts"])
        
        assert len(inactive_accounts) >= 1, (
            f"Expected at least 1 inactive account, but got {len(inactive_accounts)}. "
            f"Total accounts: {len(data['accounts'])}, "
            f"All accounts: {[(acc['id'], acc['status'], acc['role']) for acc in data['accounts']]}"
        )
        assert member_found, (
            f"Inactive member with id {sample_inactive_member.id} not found in results. "
            f"All account IDs: {[acc['id'] for acc in data['accounts']]}"
        )

    def test_list_accounts_excludes_student_and_guardian_roles(self, client: TestClient, test_org, sample_member, mock_supabase_client, db_session):
        """Ensure student and guardian records are not returned in account listing"""
        # Create guardian profile/member
        guardian_user_id = uuid4()
        guardian_profile = Profile(
            id=guardian_user_id,
            full_name="Guardian User",
            email="guardian@example.com",
            has_completed_profile=True,
            city="Springfield",
            state="IL",
            is_active=True
        )
        db_session.add(guardian_profile)
        guardian_member = OrganizationMember(
            id=uuid4(),
            organization_id=test_org.id,
            user_id=guardian_user_id,
            role=OrgRole.guardian,
            status=MemberStatus.active
        )
        db_session.add(guardian_member)

        # Create student profile/member
        student_user_id = uuid4()
        student_profile = Profile(
            id=student_user_id,
            full_name="Student User",
            email="student@example.com",
            grade_level="10",
            student_id="STU999",
            has_completed_profile=True,
            city="Springfield",
            state="IL",
            is_active=True
        )
        db_session.add(student_profile)
        student_member = OrganizationMember(
            id=uuid4(),
            organization_id=test_org.id,
            user_id=student_user_id,
            role=OrgRole.student,
            status=MemberStatus.active
        )
        db_session.add(student_member)
        db_session.commit()

        # Mock Supabase for the staff member only
        mock_user = type('obj', (object,), {
            'id': sample_member.user_id,
            'email': 'staff@example.com'
        })()
        mock_supabase_client.auth.admin.list_users.return_value = [mock_user]

        response = client.get(f"/api/v1/organizations/{test_org.id}/members")

        assert response.status_code == 200
        data = response.json()
        roles = {acc["role"] for acc in data["accounts"]}
        assert "guardian" not in roles
        assert "student" not in roles
        assert "staff" in roles or "admin" in roles
    
    def test_list_accounts_invalid_status_filter(self, client: TestClient, test_org):
        """Test listing accounts with invalid status filter"""
        response = client.get(
            f"/api/v1/organizations/{test_org.id}/members",
            params={"status_filter": "invalid_status"}
        )
        
        assert response.status_code == 400
        assert "Invalid status filter" in response.json()["detail"]
    
    def test_list_accounts_with_pagination(self, client: TestClient, db_session, test_org):
        """Test listing accounts with pagination"""
        # Create multiple members
        members = []
        for i in range(15):
            user_id = uuid4()
            profile = Profile(
                id=user_id,
                full_name=f"User {i}",
                email=f"user{i}@example.com",
                has_completed_profile=True,
                phone=f"(555) {100+i:03d}-{2000+i:04d}",
                city="Springfield",
                state="IL",
                is_active=True
            )
            db_session.add(profile)
            
            member = OrganizationMember(
                id=uuid4(),
                organization_id=test_org.id,
                user_id=user_id,
                role=OrgRole.staff,
                status=MemberStatus.active,
                joined_at=datetime.utcnow()
            )
            db_session.add(member)
            members.append(member)
        
        db_session.commit()
        
        # Test pagination
        response = client.get(
            f"/api/v1/organizations/{test_org.id}/members",
            params={"page": 2, "per_page": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["per_page"] == 10
        assert data["total"] >= 15
        assert data["total_pages"] >= 2
    
    def test_delete_account_success_soft_delete(self, client: TestClient, db_session, test_org, sample_member):
        """Test successful soft deletion (deactivation) of account"""
        # Make sure the member's user_id is different from admin's user_id
        assert sample_member.user_id != test_org.id  # Different from admin
        assert sample_member.status == MemberStatus.active
        
        response = client.delete(f"/api/v1/organizations/{test_org.id}/members/{sample_member.id}")
        
        assert response.status_code == 200
        assert "deactivated successfully" in response.json()["message"].lower()
        
        # Verify soft delete: status set to inactive, not hard deleted
        db_session.refresh(sample_member)
        assert sample_member.status == MemberStatus.inactive
        # Verify member still exists in DB
        member = db_session.query(OrganizationMember).filter(
            OrganizationMember.id == sample_member.id
        ).first()
        assert member is not None
    
    def test_delete_account_not_found(self, client: TestClient, test_org):
        """Test delete account when account not found"""
        fake_id = uuid4()
        response = client.delete(f"/api/v1/organizations/{test_org.id}/members/{fake_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_delete_account_prevents_self_deletion(self, client: TestClient, db_session, test_org, mock_user):
        """Test delete account prevents admin from deleting themselves"""
        # Get the admin member
        admin_member = db_session.query(OrganizationMember).filter(
            OrganizationMember.organization_id == test_org.id,
            OrganizationMember.user_id == mock_user.id
        ).first()
        
        assert admin_member is not None
        assert admin_member.status == MemberStatus.active
        
        # Try to delete self
        response = client.delete(f"/api/v1/organizations/{test_org.id}/members/{admin_member.id}")
        
        assert response.status_code == 400
        assert "Cannot delete your own account" in response.json()["detail"]
        
        # Verify status was not changed
        db_session.refresh(admin_member)
        assert admin_member.status == MemberStatus.active
    
    def test_list_accounts_empty_result(self, client: TestClient, db_session, mock_user, mock_supabase_client):
        """Test listing accounts with only admin member"""
        # Create a new org with only admin
        new_org = Organization(id=uuid4(), name="Empty Organization")
        db_session.add(new_org)
        
        admin_member = OrganizationMember(
            organization_id=new_org.id,
            user_id=mock_user.id,
            role=OrgRole.admin,
            status=MemberStatus.active
        )
        db_session.add(admin_member)
        
        admin_profile = Profile(
            id=mock_user.id,
            full_name="Admin User",
            email=mock_user.email,
            has_completed_profile=True,
            phone="(555) 123-4567",
            city="Springfield",
            state="IL",
            is_active=True
        )
        db_session.add(admin_profile)
        db_session.commit()
        
        response = client.get(f"/api/v1/organizations/{new_org.id}/members")
        
        assert response.status_code == 200
        data = response.json()
        # Should only have the admin member
        assert data["total"] == 1
        assert len(data["accounts"]) == 1
        assert data["accounts"][0]["role"] == "admin"
