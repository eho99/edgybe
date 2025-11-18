import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.models import Invitation, Profile, InvitationStatus, OrgRole, Organization, OrganizationMember, MemberStatus


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
    
    # Create inviter profile
    inviter_profile = Profile(
        id=mock_user.id,
        full_name="Admin User",
        has_completed_profile=True
    )
    db_session.add(inviter_profile)
    
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture
def sample_invitation(db_session, test_org, mock_user):
    """Create a sample invitation in the database."""
    invitation = Invitation(
        id=uuid4(),
        organization_id=test_org.id,
        email="test@example.com",
        role=OrgRole.staff,
        inviter_id=mock_user.id,
        status=InvitationStatus.pending,
        sent_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(invitation)
    db_session.commit()
    db_session.refresh(invitation)
    return invitation


class TestInvitationEndpoints:
    
    def test_list_invitations_success(self, client: TestClient, test_org, sample_invitation):
        """Test successful listing of invitations"""
        response = client.get(f"/api/v1/organizations/{test_org.id}/invitations")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["invitations"]) == 1
        assert data["invitations"][0]["email"] == "test@example.com"
        assert data["invitations"][0]["status"] == "pending"
        assert data["invitations"][0]["inviter_name"] == "Admin User"
        assert data["page"] == 1
        assert data["per_page"] == 10
    
    def test_list_invitations_with_filters(self, client: TestClient, db_session, test_org, sample_invitation):
        """Test listing invitations with status filter and search"""
        # Create another invitation with different status
        accepted_invitation = Invitation(
            id=uuid4(),
            organization_id=test_org.id,
            email="accepted@example.com",
            role=OrgRole.staff,
            inviter_id=sample_invitation.inviter_id,
            status=InvitationStatus.accepted,
            sent_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db_session.add(accepted_invitation)
        db_session.commit()
        
        # Test with status filter
        response = client.get(
            f"/api/v1/organizations/{test_org.id}/invitations",
            params={"status_filter": "pending"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert all(inv["status"] == "pending" for inv in data["invitations"])
        
        # Test with search
        response = client.get(
            f"/api/v1/organizations/{test_org.id}/invitations",
            params={"search": "test@example.com"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["invitations"][0]["email"] == "test@example.com"
    
    def test_list_invitations_invalid_status_filter(self, client: TestClient, test_org):
        """Test listing invitations with invalid status filter"""
        response = client.get(
            f"/api/v1/organizations/{test_org.id}/invitations",
            params={"status_filter": "invalid_status"}
        )
        
        assert response.status_code == 400
        assert "Invalid status filter" in response.json()["detail"]
    
    def test_get_invitation_stats(self, client: TestClient, db_session, test_org):
        """Test getting invitation statistics"""
        # Create invitations with different statuses
        invitations = [
            Invitation(
                id=uuid4(),
                organization_id=test_org.id,
                email=f"pending{i}@example.com",
                role=OrgRole.staff,
                inviter_id=uuid4(),
                status=InvitationStatus.pending,
                sent_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            ) for i in range(2)
        ]
        invitations.extend([
            Invitation(
                id=uuid4(),
                organization_id=test_org.id,
                email=f"accepted{i}@example.com",
                role=OrgRole.staff,
                inviter_id=uuid4(),
                status=InvitationStatus.accepted,
                sent_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            ) for i in range(5)
        ])
        invitations.append(
            Invitation(
                id=uuid4(),
                organization_id=test_org.id,
                email="expired@example.com",
                role=OrgRole.staff,
                inviter_id=uuid4(),
                status=InvitationStatus.expired,
                sent_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
        )
        
        for inv in invitations:
            db_session.add(inv)
        db_session.commit()
        
        response = client.get(f"/api/v1/organizations/{test_org.id}/invitations/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["pending"] == 2
        assert data["accepted"] == 5
        assert data["expired"] == 1
        assert data["cancelled"] == 0
        assert data["total"] == 8
    
    def test_resend_invitation_success(self, client: TestClient, sample_invitation, test_org, mock_supabase_client):
        """Test successful resend of invitation"""
        # Mock Supabase invite response - the service doesn't use the return value, just checks for exceptions
        # So we can return any value or None
        mock_supabase_client.auth.admin.invite_user_by_email.return_value = None
        
        response = client.post(f"/api/v1/organizations/{test_org.id}/invitations/{sample_invitation.id}/resend")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["status"] == "pending"
        # Verify Supabase was called
        mock_supabase_client.auth.admin.invite_user_by_email.assert_called_once()
    
    def test_resend_invitation_not_found(self, client: TestClient, test_org):
        """Test resend invitation when invitation not found"""
        fake_id = uuid4()
        response = client.post(f"/api/v1/organizations/{test_org.id}/invitations/{fake_id}/resend")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_resend_invitation_wrong_status(self, client: TestClient, db_session, test_org, sample_invitation):
        """Test resend invitation when invitation is not pending"""
        # Change status to accepted
        sample_invitation.status = InvitationStatus.accepted
        db_session.commit()
        
        response = client.post(f"/api/v1/organizations/{test_org.id}/invitations/{sample_invitation.id}/resend")
        
        assert response.status_code == 400
        assert "status" in response.json()["detail"].lower()
    
    def test_cancel_invitation_success(self, client: TestClient, db_session, sample_invitation, test_org):
        """Test successful cancellation of invitation"""
        assert sample_invitation.status == InvitationStatus.pending
        
        response = client.delete(f"/api/v1/organizations/{test_org.id}/invitations/{sample_invitation.id}")
        
        assert response.status_code == 200
        assert "cancelled successfully" in response.json()["message"].lower()
        
        # Verify status changed in DB
        db_session.refresh(sample_invitation)
        assert sample_invitation.status == InvitationStatus.cancelled
    
    def test_cancel_invitation_not_found(self, client: TestClient, test_org):
        """Test cancel invitation when invitation not found"""
        fake_id = uuid4()
        response = client.delete(f"/api/v1/organizations/{test_org.id}/invitations/{fake_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_cancel_invitation_non_pending(self, client: TestClient, db_session, sample_invitation, test_org):
        """Test cancel invitation when invitation is not pending"""
        # Change status to accepted
        sample_invitation.status = InvitationStatus.accepted
        db_session.commit()
        
        response = client.delete(f"/api/v1/organizations/{test_org.id}/invitations/{sample_invitation.id}")
        
        assert response.status_code == 400
        assert "pending" in response.json()["detail"].lower()
