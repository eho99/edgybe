import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from uuid import uuid4

from app.main import app
from app.models import Invitation, Profile, InvitationStatus, OrgRole
from app.schemas.auth import AuthenticatedMember, SupabaseUser


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_auth_member():
    return AuthenticatedMember(
        user=SupabaseUser(id=uuid4(), email="admin@example.com"),
        org_id=uuid4(),
        role=OrgRole.admin
    )


@pytest.fixture
def sample_invitation():
    return Invitation(
        id=uuid4(),
        organization_id=uuid4(),
        email="test@example.com",
        role=OrgRole.staff,
        inviter_id=uuid4(),
        status=InvitationStatus.pending,
        sent_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=7),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def sample_inviter():
    return Profile(
        id=uuid4(),
        full_name="Admin User",
        has_completed_profile=True
    )


class TestInvitationEndpoints:
    
    @patch('app.routers.invitations.auth.require_admin_role')
    @patch('app.routers.invitations.get_db')
    def test_list_invitations_success(self, mock_get_db, mock_require_admin, client, mock_auth_member, sample_invitation, sample_inviter):
        """Test successful listing of invitations"""
        # Setup
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_require_admin.return_value = mock_auth_member
        
        # Mock database queries
        mock_db.query.return_value.filter.return_value.count.return_value = 1
        mock_db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = [sample_invitation]
        mock_db.query.return_value.filter.return_value.first.return_value = sample_inviter
        
        # Execute
        response = client.get(f"/api/v1/organizations/{mock_auth_member.org_id}/invitations")
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["invitations"]) == 1
        assert data["invitations"][0]["email"] == "test@example.com"
        assert data["invitations"][0]["status"] == "pending"
        assert data["invitations"][0]["inviter_name"] == "Admin User"
    
    @patch('app.routers.invitations.auth.require_admin_role')
    @patch('app.routers.invitations.get_db')
    def test_list_invitations_with_filters(self, mock_get_db, mock_require_admin, client, mock_auth_member, sample_invitation):
        """Test listing invitations with status filter and search"""
        # Setup
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_require_admin.return_value = mock_auth_member
        
        mock_db.query.return_value.filter.return_value.count.return_value = 1
        mock_db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = [sample_invitation]
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Execute with filters
        response = client.get(
            f"/api/v1/organizations/{mock_auth_member.org_id}/invitations",
            params={
                "status_filter": "pending",
                "search": "test@example.com",
                "page": 1,
                "per_page": 10
            }
        )
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 10
    
    @patch('app.routers.invitations.auth.require_admin_role')
    @patch('app.routers.invitations.get_db')
    def test_list_invitations_invalid_status_filter(self, mock_get_db, mock_require_admin, client, mock_auth_member):
        """Test listing invitations with invalid status filter"""
        # Setup
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_require_admin.return_value = mock_auth_member
        
        # Execute with invalid status
        response = client.get(
            f"/api/v1/organizations/{mock_auth_member.org_id}/invitations",
            params={"status_filter": "invalid_status"}
        )
        
        # Verify
        assert response.status_code == 400
        assert "Invalid status filter" in response.json()["detail"]
    
    @patch('app.routers.invitations.auth.require_admin_role')
    @patch('app.routers.invitations.get_db')
    def test_get_invitation_stats(self, mock_get_db, mock_require_admin, client, mock_auth_member):
        """Test getting invitation statistics"""
        # Setup
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_require_admin.return_value = mock_auth_member
        
        # Mock count queries for different statuses
        mock_db.query.return_value.filter.return_value.count.side_effect = [2, 5, 1, 0]  # pending, accepted, expired, cancelled
        
        # Execute
        response = client.get(f"/api/v1/organizations/{mock_auth_member.org_id}/invitations/stats")
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["pending"] == 2
        assert data["accepted"] == 5
        assert data["expired"] == 1
        assert data["cancelled"] == 0
        assert data["total"] == 8
    
    @patch('app.routers.invitations.auth.require_admin_role')
    @patch('app.routers.invitations.get_invitation_service')
    @patch('app.routers.invitations.get_db')
    def test_resend_invitation_success(self, mock_get_db, mock_get_service, mock_require_admin, client, mock_auth_member, sample_invitation, sample_inviter):
        """Test successful resend of invitation"""
        # Setup
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_require_admin.return_value = mock_auth_member
        
        # Mock invitation service
        mock_service = MagicMock()
        mock_service.resend_invitation = MagicMock(return_value=(True, "Invitation resent successfully"))
        mock_get_service.return_value = mock_service
        
        # Mock database queries for fetching invitation after resend
        mock_db.query.return_value.filter.return_value.first.side_effect = [sample_invitation, sample_inviter]
        
        # Execute
        response = client.post(f"/api/v1/organizations/{mock_auth_member.org_id}/invitations/{sample_invitation.id}/resend")
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["status"] == "pending"
        mock_service.resend_invitation.assert_called_once_with(
            invitation_id=sample_invitation.id,
            org_id=mock_auth_member.org_id
        )
    
    @patch('app.routers.invitations.auth.require_admin_role')
    @patch('app.routers.invitations.get_invitation_service')
    @patch('app.routers.invitations.get_db')
    def test_resend_invitation_not_found(self, mock_get_db, mock_get_service, mock_require_admin, client, mock_auth_member):
        """Test resend invitation when invitation not found"""
        # Setup
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_require_admin.return_value = mock_auth_member
        
        # Mock invitation service returning not found
        mock_service = MagicMock()
        mock_service.resend_invitation = MagicMock(return_value=(False, "Invitation not found"))
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.post(f"/api/v1/organizations/{mock_auth_member.org_id}/invitations/{uuid4()}/resend")
        
        # Verify
        assert response.status_code == 404
        assert "Invitation not found" in response.json()["detail"]
    
    @patch('app.routers.invitations.auth.require_admin_role')
    @patch('app.routers.invitations.get_invitation_service')
    @patch('app.routers.invitations.get_db')
    def test_resend_invitation_wrong_status(self, mock_get_db, mock_get_service, mock_require_admin, client, mock_auth_member, sample_invitation):
        """Test resend invitation when invitation is not pending"""
        # Setup
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_require_admin.return_value = mock_auth_member
        
        # Mock invitation service returning wrong status error
        mock_service = MagicMock()
        mock_service.resend_invitation = MagicMock(return_value=(False, "Cannot resend invitation with status: accepted"))
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.post(f"/api/v1/organizations/{mock_auth_member.org_id}/invitations/{sample_invitation.id}/resend")
        
        # Verify
        assert response.status_code == 400
        assert "status" in response.json()["detail"].lower()
    
    @patch('app.routers.invitations.auth.require_admin_role')
    @patch('app.routers.invitations.get_db')
    def test_cancel_invitation_success(self, mock_get_db, mock_require_admin, client, mock_auth_member, sample_invitation):
        """Test successful cancellation of invitation"""
        # Setup
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_require_admin.return_value = mock_auth_member
        
        mock_db.query.return_value.filter.return_value.first.return_value = sample_invitation
        
        # Execute
        response = client.delete(f"/api/v1/organizations/{mock_auth_member.org_id}/invitations/{sample_invitation.id}")
        
        # Verify
        assert response.status_code == 200
        assert "Invitation cancelled successfully" in response.json()["message"]
        assert sample_invitation.status == InvitationStatus.cancelled
        mock_db.commit.assert_called_once()
    
    @patch('app.routers.invitations.auth.require_admin_role')
    @patch('app.routers.invitations.get_db')
    def test_cancel_invitation_not_found(self, mock_get_db, mock_require_admin, client, mock_auth_member):
        """Test cancel invitation when invitation not found"""
        # Setup
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_require_admin.return_value = mock_auth_member
        
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Execute
        response = client.delete(f"/api/v1/organizations/{mock_auth_member.org_id}/invitations/{uuid4()}")
        
        # Verify
        assert response.status_code == 404
        assert "Invitation not found" in response.json()["detail"]


