import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from uuid import uuid4

from app.services.invitations import InvitationService
from app.models import Invitation, OrganizationMember, Profile, Organization, InvitationStatus, OrgRole, MemberStatus
from app.schemas.user import UserInviteRequest


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
class TestInvitationServiceIntegration:
    
    @patch('app.services.invitations.supabase')
    async def test_invite_new_user_creates_invitation_and_membership(self, mock_supabase, invitation_service, sample_invitation_data):
        """Test that inviting a new user creates both invitation and membership records"""
        # Setup
        mock_supabase.auth.admin.get_user_by_email.side_effect = Exception("User not found")
        mock_supabase.auth.admin.invite_user_by_email.return_value = MagicMock()
        
        # Mock database operations
        invitation_service.db.add = MagicMock()
        invitation_service.db.commit = MagicMock()
        invitation_service.db.refresh = MagicMock()
        
        # Execute
        result = await invitation_service.invite_or_add_user_to_org(
            org_id=sample_invitation_data['org_id'],
            email=sample_invitation_data['email'],
            role=sample_invitation_data['role'],
            inviter_id=sample_invitation_data['inviter_id']
        )
        
        # Verify
        assert invitation_service.db.add.call_count == 2  # Invitation + Membership
        invitation_service.db.commit.assert_called_once()
        invitation_service.db.refresh.assert_called()
        
        # Verify invitation was created
        invitation_call_args = invitation_service.db.add.call_args_list[0][0][0]
        assert invitation_call_args.organization_id == sample_invitation_data['org_id']
        assert invitation_call_args.email == sample_invitation_data['email']
        assert invitation_call_args.role == sample_invitation_data['role']
        assert invitation_call_args.inviter_id == sample_invitation_data['inviter_id']
        assert invitation_call_args.status == InvitationStatus.pending
        
        # Verify membership was created
        membership_call_args = invitation_service.db.add.call_args_list[1][0][0]
        assert membership_call_args.organization_id == sample_invitation_data['org_id']
        assert membership_call_args.user_id is None
        assert membership_call_args.invite_email == sample_invitation_data['email']
        assert membership_call_args.role == sample_invitation_data['role']


class TestInvitationModel:
    
    def test_invitation_creation(self):
        """Test creating an invitation instance"""
        invitation = Invitation(
            organization_id=uuid4(),
            email='test@example.com',
            role=OrgRole.staff,
            inviter_id=uuid4()
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