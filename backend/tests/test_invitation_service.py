import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import os

from app.services.invitations import InvitationService
from app.models import Invitation, OrganizationMember, Profile, Organization, InvitationStatus, OrgRole, MemberStatus

FRONTEND_URL = os.getenv("NEXT_PUBLIC_FRONTEND_URL", "http://localhost:3000")


@pytest.fixture
def mock_db_session():
    return MagicMock(spec=Session)


@pytest.fixture
def invitation_service(mock_db_session):
    return InvitationService(mock_db_session)


@pytest.fixture
def sample_org_id():
    return uuid4()


@pytest.fixture
def sample_inviter_id():
    return uuid4()


@pytest.fixture
def sample_invitation_data():
    return {
        'org_id': uuid4(),
        'email': 'test@example.com',
        'role': OrgRole.staff,
        'inviter_id': uuid4()
    }


class TestInvitationService:
    
    def test_mark_invitation_accepted_success(self, invitation_service, mock_db_session):
        """Test successfully marking invitation as accepted"""
        # Setup
        email = 'test@example.com'
        user_id = uuid4()
        
        # Mock pending invitation
        mock_invitation = MagicMock()
        mock_invitation.status = InvitationStatus.pending
        mock_invitation.accepted_at = None
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_invitation]
        
        # Execute
        result = invitation_service.mark_invitation_accepted(email, user_id)
        
        # Verify
        assert result is True
        assert mock_invitation.status == InvitationStatus.accepted
        assert mock_invitation.accepted_at is not None
        mock_db_session.commit.assert_called_once()
    
    def test_mark_invitation_accepted_no_pending_invitations(self, invitation_service, mock_db_session):
        """Test marking invitation as accepted when no pending invitations exist"""
        # Setup
        email = 'test@example.com'
        user_id = uuid4()
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = []
        
        # Execute
        result = invitation_service.mark_invitation_accepted(email, user_id)
        
        # Verify
        assert result is False
        mock_db_session.commit.assert_not_called()
    
    def test_mark_invitation_accepted_exception(self, invitation_service, mock_db_session):
        """Test handling exception when marking invitation as accepted"""
        # Setup
        email = 'test@example.com'
        user_id = uuid4()
        
        mock_db_session.query.side_effect = Exception("Database error")
        
        # Execute
        result = invitation_service.mark_invitation_accepted(email, user_id)
        
        # Verify
        assert result is False
    
    def test_link_invited_user_to_organization_by_email(self, invitation_service, mock_db_session):
        """Test linking user to organization by invite_email"""
        # Setup
        user_id = uuid4()
        email = 'test@example.com'
        org_id = uuid4()
        
        # Mock pending membership
        mock_membership = MagicMock()
        mock_membership.user_id = None
        mock_membership.invite_email = email
        mock_membership.organization_id = org_id
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_membership]
        
        # Execute
        result = invitation_service.link_invited_user_to_organization(user_id, email)
        
        # Verify
        assert result == mock_membership
        assert mock_membership.user_id == user_id
        assert mock_membership.invite_email is None
        mock_db_session.commit.assert_called_once()
    
    def test_link_invited_user_to_organization_no_memberships(self, invitation_service, mock_db_session):
        """Test linking when no memberships found"""
        # Setup
        user_id = uuid4()
        email = 'test@example.com'
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = []
        
        # Execute
        result = invitation_service.link_invited_user_to_organization(user_id, email)
        
        # Verify
        assert result is None
        mock_db_session.commit.assert_not_called()


@pytest.mark.asyncio
class TestResendInvitation:
    
    @patch('app.services.invitations.supabase')
    async def test_resend_invitation_success(self, mock_supabase, invitation_service, mock_db_session):
        """Test successful resend of pending invitation"""
        # Setup
        invitation_id = uuid4()
        org_id = uuid4()
        email = 'test@example.com'
        
        # Mock invitation
        mock_invitation = MagicMock()
        mock_invitation.id = invitation_id
        mock_invitation.organization_id = org_id
        mock_invitation.email = email
        mock_invitation.status = InvitationStatus.pending
        mock_invitation.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        mock_invitation.sent_at = datetime.now(timezone.utc) - timedelta(days=1)
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_invitation
        mock_supabase.auth.admin.invite_user_by_email.return_value = MagicMock()
        
        # Execute
        success, message = await invitation_service.resend_invitation(invitation_id, org_id)
        
        # Verify
        assert success is True
        assert "successfully" in message.lower()
        mock_supabase.auth.admin.invite_user_by_email.assert_called_once_with(
            email,
            options={"redirect_to": FRONTEND_URL + "/invite-profile-completion"}
        )
        assert mock_invitation.sent_at is not None
        mock_db_session.commit.assert_called_once()
    
    @patch('app.services.invitations.supabase')
    async def test_resend_invitation_extends_expiration(self, mock_supabase, invitation_service, mock_db_session):
        """Test that resending expired invitation extends expiration"""
        # Setup
        invitation_id = uuid4()
        org_id = uuid4()
        email = 'test@example.com'
        
        # Mock expired invitation
        mock_invitation = MagicMock()
        mock_invitation.id = invitation_id
        mock_invitation.organization_id = org_id
        mock_invitation.email = email
        mock_invitation.status = InvitationStatus.pending
        mock_invitation.expires_at = datetime.now(timezone.utc) - timedelta(days=1)  # Expired
        mock_invitation.sent_at = datetime.now(timezone.utc) - timedelta(days=8)
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_invitation
        mock_supabase.auth.admin.invite_user_by_email.return_value = MagicMock()
        
        # Execute
        success, message = await invitation_service.resend_invitation(invitation_id, org_id)
        
        # Verify
        assert success is True
        # Verify expiration was extended (should be ~7 days from now)
        assert mock_invitation.expires_at > datetime.now(timezone.utc)
        mock_db_session.commit.assert_called_once()
    
    async def test_resend_invitation_not_found(self, invitation_service, mock_db_session):
        """Test resend when invitation not found"""
        # Setup
        invitation_id = uuid4()
        org_id = uuid4()
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Execute
        success, message = await invitation_service.resend_invitation(invitation_id, org_id)
        
        # Verify
        assert success is False
        assert "not found" in message.lower()
        mock_db_session.commit.assert_not_called()
    
    async def test_resend_invitation_wrong_status(self, invitation_service, mock_db_session):
        """Test resend fails for non-pending invitations"""
        # Setup
        invitation_id = uuid4()
        org_id = uuid4()
        
        # Mock accepted invitation
        mock_invitation = MagicMock()
        mock_invitation.id = invitation_id
        mock_invitation.organization_id = org_id
        mock_invitation.status = InvitationStatus.accepted
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_invitation
        
        # Execute
        success, message = await invitation_service.resend_invitation(invitation_id, org_id)
        
        # Verify
        assert success is False
        assert "status" in message.lower()
        mock_db_session.commit.assert_not_called()
    
    @patch('app.services.invitations.supabase')
    async def test_resend_invitation_supabase_api_error(self, mock_supabase, invitation_service, mock_db_session):
        """Test handling Supabase API errors"""
        from supabase_auth.errors import AuthApiError
        
        # Setup
        invitation_id = uuid4()
        org_id = uuid4()
        email = 'test@example.com'
        
        # Mock invitation
        mock_invitation = MagicMock()
        mock_invitation.id = invitation_id
        mock_invitation.organization_id = org_id
        mock_invitation.email = email
        mock_invitation.status = InvitationStatus.pending
        mock_invitation.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_invitation
        
        # Mock Supabase API error - use real AuthApiError class
        mock_supabase.auth.admin.invite_user_by_email.side_effect = AuthApiError("Rate limit exceeded", 429, "rate_limit_exceeded")
        
        # Execute
        success, message = await invitation_service.resend_invitation(invitation_id, org_id)
        
        # Verify
        assert success is False
        assert "rate limit" in message.lower() or "failed" in message.lower()
        mock_db_session.commit.assert_not_called()
    
    @patch('app.services.invitations.supabase')
    async def test_resend_invitation_user_already_exists(self, mock_supabase, invitation_service, mock_db_session):
        """Test handling user already exists in Auth"""
        from supabase_auth.errors import AuthApiError
        
        # Setup
        invitation_id = uuid4()
        org_id = uuid4()
        email = 'test@example.com'
        
        # Mock invitation
        mock_invitation = MagicMock()
        mock_invitation.id = invitation_id
        mock_invitation.organization_id = org_id
        mock_invitation.email = email
        mock_invitation.status = InvitationStatus.pending
        mock_invitation.expires_at = datetime.now(timezone.utc) - timedelta(days=1)  # Expired
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_invitation
        
        # Mock Supabase error indicating user already exists - use real AuthApiError
        error = AuthApiError("User already registered", 400, "user_already_exists")
        mock_supabase.auth.admin.invite_user_by_email.side_effect = error
        
        # Execute
        success, message = await invitation_service.resend_invitation(invitation_id, org_id)
        
        # Verify
        assert success is True  # Should still succeed, just update timestamp
        assert "already exists" in message.lower() or "timestamp updated" in message.lower()
        assert mock_invitation.sent_at is not None
        mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
class TestReactivationFlow:
    """Tests for reactivating inactive memberships when re-inviting users"""
    
    @patch('app.services.invitations.supabase')
    async def test_reactivate_inactive_member(self, mock_supabase, invitation_service, mock_db_session):
        """Test that re-inviting a user with inactive membership reactivates them"""
        # Setup
        org_id = uuid4()
        user_id = uuid4()
        email = 'reactivate@example.com'
        role = OrgRole.staff
        inviter_id = uuid4()

        # Mock Supabase user - service converts string UUIDs to UUID objects
        mock_supabase_user = MagicMock()
        mock_supabase_user.id = str(user_id)  # Supabase returns string UUIDs
        mock_supabase_user.email = email
        
        mock_auth_response = MagicMock()
        mock_auth_response.data = [mock_supabase_user]
        mock_supabase.auth.admin.list_users.return_value = mock_auth_response
        
        # Mock existing profile
        mock_profile = MagicMock()
        mock_profile.id = user_id  # Service converts to UUID, so use UUID here
        mock_profile.full_name = "Test User"
        mock_profile.has_completed_profile = True
        
        # Mock inactive membership - this is what needs to be found by the query
        # Create a simple mock object that allows attribute assignment
        # We'll use a simple object that tracks attribute changes
        # Import the models to ensure we're using the same enum
        from app.models import MemberStatus as ModelsMemberStatus
        class MockMember:
            def __init__(self):
                self.user_id = user_id
                self.organization_id = org_id
                # Use the same enum that the service uses
                self.status = ModelsMemberStatus.inactive
                self.role = OrgRole.staff
        
        mock_inactive_member = MockMember()
        
        # Setup query chain - service makes TWO separate queries:
        # 1. db.query(Profile).filter(Profile.id == user_id).first()
        # 2. db.query(OrganizationMember).filter(user_id == user_id, org_id == org_id).first()
        query_call_count = {'count': 0}  # Track which query we're on
        
        def query_side_effect(model):
            query_mock = MagicMock()
            filter_mock = MagicMock()
            
            if model == Profile:
                # First query: Profile lookup
                filter_mock.first.return_value = mock_profile
            elif model == OrganizationMember:
                # Second query: OrganizationMember lookup (this is the reactivation check)
                filter_mock.first.return_value = mock_inactive_member
            
            query_mock.filter.return_value = filter_mock
            return query_mock
        
        mock_db_session.query.side_effect = query_side_effect
        # Ensure the service uses the updated mock_db_session
        invitation_service.db = mock_db_session
        
        # Execute
        result = await invitation_service.invite_or_add_user_to_org(
            org_id=org_id,
            email=email,
            role=role,
            inviter_id=inviter_id
        )

        # Verify - result should be the same member object that was modified
        assert result is not None
        # The service modifies the member in place, so result should be mock_inactive_member
        assert result is mock_inactive_member
        # Verify reactivation: status changed to active
        assert mock_inactive_member.status == MemberStatus.active
        # Verify role was updated
        assert mock_inactive_member.role == role
        # Verify password reset email was sent for reactivated user
        mock_supabase.auth.reset_password_for_email.assert_called_once_with(
            email,
            {"redirect_to": FRONTEND_URL + "/reset-password"}
        )
        mock_db_session.commit.assert_called_once()
        # Verify refresh was called on the member
        mock_db_session.refresh.assert_called()
        # Verify no new membership was created (we're reactivating, not creating)
        mock_db_session.add.assert_not_called()
    
    @patch('app.services.invitations.supabase')
    async def test_reactivate_inactive_member_updates_role(self, mock_supabase, invitation_service, mock_db_session):
        """Test that reactivation updates the role correctly"""
        # Setup
        org_id = uuid4()
        user_id = uuid4()
        email = 'reactivate@example.com'
        new_role = OrgRole.secretary  # Different role
        inviter_id = uuid4()
        
        # Mock existing user in Supabase Auth - set email as real attribute
        mock_supabase_user = MagicMock()
        mock_supabase_user.id = str(user_id) if not isinstance(user_id, str) else user_id
        object.__setattr__(mock_supabase_user, 'email', email)
        
        mock_auth_response = MagicMock()
        mock_auth_response.data = [mock_supabase_user]
        mock_supabase.auth.admin.list_users.return_value = mock_auth_response
        
        # Mock existing profile - service checks has_completed_profile
        mock_profile = MagicMock()
        mock_profile.id = user_id
        mock_profile.has_completed_profile = True  # Existing user should have completed profile
        
        # Mock inactive membership with different role - set attributes as real values
        mock_inactive_member = MagicMock()
        object.__setattr__(mock_inactive_member, 'user_id', user_id)
        object.__setattr__(mock_inactive_member, 'organization_id', org_id)
        object.__setattr__(mock_inactive_member, 'status', MemberStatus.inactive)
        object.__setattr__(mock_inactive_member, 'role', OrgRole.staff)  # Old role
        
        # Setup query chain
        def query_side_effect(model):
            query_mock = MagicMock()
            filter_mock = MagicMock()
            if model == Profile:
                filter_mock.first.return_value = mock_profile
            elif model == OrganizationMember:
                filter_mock.first.return_value = mock_inactive_member
            query_mock.filter.return_value = filter_mock
            return query_mock
        
        mock_db_session.query.side_effect = query_side_effect
        invitation_service.db = mock_db_session
        
        # Execute
        result = await invitation_service.invite_or_add_user_to_org(
            org_id=org_id,
            email=email,
            role=new_role,
            inviter_id=inviter_id
        )
        
        # Verify - result is the member object that was modified
        assert result is not None
        assert result is mock_inactive_member  # Service returns the same member object it found/modified
        assert mock_inactive_member.status == MemberStatus.active
        assert mock_inactive_member.role == new_role  # Role updated
        # Verify password reset email was sent for reactivated user
        mock_supabase.auth.reset_password_for_email.assert_called_once_with(
            email,
            {"redirect_to": FRONTEND_URL + "/reset-password"}
        )
        mock_db_session.commit.assert_called_once()
    
    @patch('app.services.invitations.supabase')
    async def test_active_member_not_reactivated(self, mock_supabase, invitation_service, mock_db_session):
        """Test that active members are not reactivated, just role updated"""
        # Setup
        org_id = uuid4()
        user_id = uuid4()
        email = 'active@example.com'
        new_role = OrgRole.secretary
        inviter_id = uuid4()
        
        # Mock existing user in Supabase Auth - set email as real attribute
        mock_supabase_user = MagicMock()
        mock_supabase_user.id = str(user_id) if not isinstance(user_id, str) else user_id
        object.__setattr__(mock_supabase_user, 'email', email)
        
        mock_auth_response = MagicMock()
        mock_auth_response.data = [mock_supabase_user]
        mock_supabase.auth.admin.list_users.return_value = mock_auth_response
        
        # Mock existing profile - service checks has_completed_profile
        mock_profile = MagicMock()
        mock_profile.id = user_id
        mock_profile.has_completed_profile = True  # Existing user should have completed profile
        
        # Mock active membership - set attributes as real values
        mock_active_member = MagicMock()
        object.__setattr__(mock_active_member, 'user_id', user_id)
        object.__setattr__(mock_active_member, 'organization_id', org_id)
        object.__setattr__(mock_active_member, 'status', MemberStatus.active)
        object.__setattr__(mock_active_member, 'role', OrgRole.staff)
        
        # Setup query chain
        def query_side_effect(model):
            query_mock = MagicMock()
            filter_mock = MagicMock()
            if model == Profile:
                filter_mock.first.return_value = mock_profile
            elif model == OrganizationMember:
                filter_mock.first.return_value = mock_active_member
            query_mock.filter.return_value = filter_mock
            return query_mock
        
        mock_db_session.query.side_effect = query_side_effect
        invitation_service.db = mock_db_session
        
        # Execute
        result = await invitation_service.invite_or_add_user_to_org(
            org_id=org_id,
            email=email,
            role=new_role,
            inviter_id=inviter_id
        )
        
        # Verify - result is the member object that was modified
        assert result is not None
        assert result is mock_active_member  # Service returns the same member object it found/modified
        # Status should remain active (not changed) - service only updates status if it was inactive
        assert mock_active_member.status == MemberStatus.active
        # Role should be updated
        assert mock_active_member.role == new_role
        mock_db_session.commit.assert_called_once()
        # Verify password reset email was NOT sent (only sent for reactivated inactive members)
        mock_supabase.auth.reset_password_for_email.assert_not_called()

class TestInvitationModel:
    
    def test_invitation_creation(self):
        """Test creating an invitation instance"""
        from datetime import datetime, timedelta, timezone
        
        invitation = Invitation(
            organization_id=uuid4(),
            email='test@example.com',
            role=OrgRole.staff,
            inviter_id=uuid4(),
            status=InvitationStatus.pending,  # Explicitly set status since default may not apply outside DB
            sent_at=datetime.now(timezone.utc),  # server_default only applies in DB
            expires_at=datetime.now(timezone.utc) + timedelta(days=7)  # server_default only applies in DB
        )
        
        assert invitation.email == 'test@example.com'
        assert invitation.role == OrgRole.staff
        assert invitation.status == InvitationStatus.pending
        assert invitation.sent_at is not None
        assert invitation.expires_at is not None
    
    def test_invitation_repr(self):
        """Test invitation string representation"""
        invitation = Invitation(
            id=uuid4(),
            email='test@example.com',
            status=InvitationStatus.pending
        )
        
        repr_str = repr(invitation)
        assert 'test@example.com' in repr_str
        assert 'pending' in repr_str