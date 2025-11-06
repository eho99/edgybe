import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from datetime import datetime
from uuid import uuid4

from app.main import app
from app.models import OrganizationMember, Profile, MemberStatus, OrgRole
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
def sample_member():
    user_id = uuid4()
    return OrganizationMember(
        id=uuid4(),
        organization_id=uuid4(),
        user_id=user_id,
        role=OrgRole.staff,
        status=MemberStatus.active,
        joined_at=datetime.utcnow()
    )


@pytest.fixture
def sample_profile():
    user_id = uuid4()
    return Profile(
        id=user_id,
        full_name="Test User",
        has_completed_profile=True
    )


@pytest.fixture
def sample_inactive_member():
    user_id = uuid4()
    return OrganizationMember(
        id=uuid4(),
        organization_id=uuid4(),
        user_id=user_id,
        role=OrgRole.student,
        status=MemberStatus.inactive,
        joined_at=datetime.utcnow()
    )


class TestAccountManagementEndpoints:
    
    @patch('app.routers.members.auth.require_admin_role')
    @patch('app.routers.members.get_db')
    @patch('app.routers.members.supabase')
    def test_list_accounts_success(self, mock_supabase, mock_get_db, mock_require_admin, client, mock_auth_member, sample_member, sample_profile):
        """Test successful listing of accounts"""
        # Setup
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_require_admin.return_value = mock_auth_member
        
        # Mock database queries
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.offset.return_value.limit.return_value.all.return_value = [sample_member]
        mock_query.count.return_value = 1
        mock_db.query.return_value = mock_query
        
        # Mock Supabase Auth to return user email
        mock_supabase_user = MagicMock()
        mock_supabase_user.id = sample_member.user_id
        mock_supabase_user.email = "test@example.com"
        mock_auth_response = MagicMock()
        mock_auth_response.data = [mock_supabase_user]
        mock_supabase.auth.admin.list_users.return_value = mock_auth_response
        
        # Execute
        response = client.get(f"/api/v1/organizations/{mock_auth_member.org_id}/members")
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["accounts"]) == 1
        assert data["accounts"][0]["role"] == "staff"
        assert data["accounts"][0]["status"] == "active"
        assert data["page"] == 1
        assert data["per_page"] == 10
    
    @patch('app.routers.members.auth.require_admin_role')
    @patch('app.routers.members.get_db')
    @patch('app.routers.members.supabase')
    def test_list_accounts_with_filters(self, mock_supabase, mock_get_db, mock_require_admin, client, mock_auth_member, sample_member, sample_profile):
        """Test listing accounts with status filter and search"""
        # Setup
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_require_admin.return_value = mock_auth_member
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.offset.return_value.limit.return_value.all.return_value = [sample_member]
        mock_query.count.return_value = 1
        mock_db.query.return_value = mock_query
        
        # Mock Supabase Auth
        mock_supabase_user = MagicMock()
        mock_supabase_user.id = sample_member.user_id
        mock_supabase_user.email = "test@example.com"
        mock_auth_response = MagicMock()
        mock_auth_response.data = [mock_supabase_user]
        mock_supabase.auth.admin.list_users.return_value = mock_auth_response
        
        # Execute with filters
        response = client.get(
            f"/api/v1/organizations/{mock_auth_member.org_id}/members",
            params={
                "status_filter": "active",
                "search": "test",
                "page": 1,
                "per_page": 10
            }
        )
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 10
    
    @patch('app.routers.members.auth.require_admin_role')
    @patch('app.routers.members.get_db')
    @patch('app.routers.members.supabase')
    def test_list_accounts_includes_inactive(self, mock_supabase, mock_get_db, mock_require_admin, client, mock_auth_member, sample_inactive_member):
        """Test listing accounts includes inactive members"""
        # Setup
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_require_admin.return_value = mock_auth_member
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.offset.return_value.limit.return_value.all.return_value = [sample_inactive_member]
        mock_query.count.return_value = 1
        mock_db.query.return_value = mock_query
        
        # Mock Supabase Auth
        mock_supabase_user = MagicMock()
        mock_supabase_user.id = sample_inactive_member.user_id
        mock_supabase_user.email = "inactive@example.com"
        mock_auth_response = MagicMock()
        mock_auth_response.data = [mock_supabase_user]
        mock_supabase.auth.admin.list_users.return_value = mock_auth_response
        
        # Execute
        response = client.get(f"/api/v1/organizations/{mock_auth_member.org_id}/members")
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert len(data["accounts"]) == 1
        assert data["accounts"][0]["status"] == "inactive"
    
    @patch('app.routers.members.auth.require_admin_role')
    @patch('app.routers.members.get_db')
    def test_list_accounts_invalid_status_filter(self, mock_get_db, mock_require_admin, client, mock_auth_member):
        """Test listing accounts with invalid status filter"""
        # Setup
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_require_admin.return_value = mock_auth_member
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_db.query.return_value = mock_query
        
        # Execute with invalid status
        response = client.get(
            f"/api/v1/organizations/{mock_auth_member.org_id}/members",
            params={"status_filter": "invalid_status"}
        )
        
        # Verify
        assert response.status_code == 400
        assert "Invalid status filter" in response.json()["detail"]
    
    @patch('app.routers.members.auth.require_admin_role')
    @patch('app.routers.members.get_db')
    @patch('app.routers.members.supabase')
    def test_list_accounts_with_pagination(self, mock_supabase, mock_get_db, mock_require_admin, client, mock_auth_member, sample_member):
        """Test listing accounts with pagination"""
        # Setup
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_require_admin.return_value = mock_auth_member
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.offset.return_value.limit.return_value.all.return_value = [sample_member]
        mock_query.count.return_value = 25  # Total 25 accounts
        mock_db.query.return_value = mock_query
        
        # Mock Supabase Auth
        mock_supabase_user = MagicMock()
        mock_supabase_user.id = sample_member.user_id
        mock_supabase_user.email = "test@example.com"
        mock_auth_response = MagicMock()
        mock_auth_response.data = [mock_supabase_user]
        mock_supabase.auth.admin.list_users.return_value = mock_auth_response
        
        # Execute with pagination
        response = client.get(
            f"/api/v1/organizations/{mock_auth_member.org_id}/members",
            params={"page": 2, "per_page": 10}
        )
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 25
        assert data["total_pages"] == 3  # 25 / 10 = 3 pages
        assert data["page"] == 2
    
    @patch('app.routers.members.auth.require_admin_role')
    @patch('app.routers.members.get_db')
    def test_delete_account_success(self, mock_get_db, mock_require_admin, client, mock_auth_member, sample_member):
        """Test successful deletion of account"""
        # Setup
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_require_admin.return_value = mock_auth_member
        
        # Make sure the member's user_id is different from admin's user_id
        sample_member.user_id = uuid4()  # Different from admin user_id
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = sample_member
        mock_db.query.return_value = mock_query
        
        # Execute
        response = client.delete(f"/api/v1/organizations/{mock_auth_member.org_id}/members/{sample_member.id}")
        
        # Verify
        assert response.status_code == 200
        assert "Account deleted successfully" in response.json()["message"]
        mock_db.delete.assert_called_once_with(sample_member)
        mock_db.commit.assert_called_once()
    
    @patch('app.routers.members.auth.require_admin_role')
    @patch('app.routers.members.get_db')
    def test_delete_account_not_found(self, mock_get_db, mock_require_admin, client, mock_auth_member):
        """Test delete account when account not found"""
        # Setup
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_require_admin.return_value = mock_auth_member
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # Execute
        response = client.delete(f"/api/v1/organizations/{mock_auth_member.org_id}/members/{uuid4()}")
        
        # Verify
        assert response.status_code == 404
        assert "Account not found" in response.json()["detail"]
    
    @patch('app.routers.members.auth.require_admin_role')
    @patch('app.routers.members.get_db')
    def test_delete_account_prevents_self_deletion(self, mock_get_db, mock_require_admin, client, mock_auth_member, sample_member):
        """Test delete account prevents admin from deleting themselves"""
        # Setup
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_require_admin.return_value = mock_auth_member
        
        # Set the member's user_id to match admin's user_id (self-deletion attempt)
        sample_member.user_id = mock_auth_member.user.id
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = sample_member
        mock_db.query.return_value = mock_query
        
        # Execute
        response = client.delete(f"/api/v1/organizations/{mock_auth_member.org_id}/members/{sample_member.id}")
        
        # Verify
        assert response.status_code == 400
        assert "Cannot delete your own account" in response.json()["detail"]
        mock_db.delete.assert_not_called()
    
    @patch('app.routers.members.auth.require_admin_role')
    @patch('app.routers.members.get_db')
    @patch('app.routers.members.supabase')
    def test_list_accounts_empty_result(self, mock_supabase, mock_get_db, mock_require_admin, client, mock_auth_member):
        """Test listing accounts with no results"""
        # Setup
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_require_admin.return_value = mock_auth_member
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.offset.return_value.limit.return_value.all.return_value = []
        mock_query.count.return_value = 0
        mock_db.query.return_value = mock_query
        
        # Execute
        response = client.get(f"/api/v1/organizations/{mock_auth_member.org_id}/members")
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["accounts"]) == 0
        assert data["total_pages"] == 0

