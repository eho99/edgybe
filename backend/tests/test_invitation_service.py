import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from supabase_auth.errors import AuthApiError

from app.services.invitations import InvitationService
from app.models import Profile, OrganizationMember, OrgRole, Organization

# Mock user data
mock_new_user_email = "new.user@example.com"
mock_existing_auth_user_email = "existing.auth@example.com"
mock_existing_auth_user = MagicMock()
mock_existing_auth_user.user.id = "uuid-for-existing-auth-user"
mock_existing_auth_user.user.email = mock_existing_auth_user_email

mock_new_invite_response = MagicMock()
mock_new_invite_response.user.id = "uuid-for-new-user"

@pytest.mark.asyncio
async def test_invite_new_user(
    db_session: Session, 
    mock_supabase_client: MagicMock
):
    """
    Test inviting a user who does NOT exist in Supabase Auth.
    """
    # Create test organization
    test_org = Organization(id="uuid-for-org", name="Test Org")
    db_session.add(test_org)
    db_session.commit()
    
    # 1. Setup Mocks
    mock_supabase_client.auth.admin.get_user_by_email.side_effect = AuthApiError(message="User not found")
    mock_supabase_client.auth.admin.invite_user_by_email.return_value = mock_new_invite_response
    
    with patch('app.services.invitations.supabase', mock_supabase_client):
        service = InvitationService(db_session)
        
        # 2. Run Service
        member = await service.invite_or_add_user_to_org(
            org_id="uuid-for-org",
            email=mock_new_user_email,
            role=OrgRole.member,
            full_name="New User"
        )
        
        # 3. Assertions
        # Check Supabase admin calls
        mock_supabase_client.auth.admin.get_user_by_email.assert_called_with(mock_new_user_email)
        mock_supabase_client.auth.admin.invite_user_by_email.assert_called_with(mock_new_user_email)
        
        # Check DB
        assert member.user_id == "uuid-for-new-user"
        assert member.organization_id == "uuid-for-org"
        assert member.role == OrgRole.member
        
        profile = db_session.query(Profile).filter(Profile.id == "uuid-for-new-user").first()
        assert profile is not None
        assert profile.full_name == "New User"
        assert profile.has_completed_profile is False

@pytest.mark.asyncio
async def test_add_existing_auth_user_to_org(
    db_session: Session, 
    mock_supabase_client: MagicMock
):
    """
    Test adding a user who exists in Auth but is not in the org.
    """
    # Create test organization
    test_org = Organization(id="uuid-for-org-2", name="Test Org 2")
    db_session.add(test_org)
    db_session.commit()
    
    # 1. Setup Mocks
    mock_supabase_client.auth.admin.get_user_by_email.return_value = mock_existing_auth_user
    
    # Pre-seed the DB with a profile for this existing user
    existing_profile = Profile(
        id="uuid-for-existing-auth-user", 
        full_name="Existing User", 
        has_completed_profile=False
    )
    db_session.add(existing_profile)
    db_session.commit()
    
    with patch('app.services.invitations.supabase', mock_supabase_client):
        service = InvitationService(db_session)
        
        # 2. Run Service
        member = await service.invite_or_add_user_to_org(
            org_id="uuid-for-org-2",
            email=mock_existing_auth_user_email,
            role=OrgRole.admin,
            full_name="This name should be ignored if profile exists"
        )
        
        # 3. Assertions
        mock_supabase_client.auth.admin.get_user_by_email.assert_called_with(mock_existing_auth_user_email)
        mock_supabase_client.auth.admin.invite_user_by_email.assert_not_called()
        
        assert member.user_id == "uuid-for-existing-auth-user"
        assert member.organization_id == "uuid-for-org-2"
        assert member.role == OrgRole.admin
        
        db_member = db_session.query(OrganizationMember).filter(
            OrganizationMember.user_id == "uuid-for-existing-auth-user"
        ).first()
        assert db_member is not None

@pytest.mark.asyncio
async def test_update_existing_member_role(
    db_session: Session, 
    mock_supabase_client: MagicMock
):
    """
    Test "inviting" a user who is already a member of the org.
    It should just update their role.
    """
    # Create test organization
    test_org = Organization(id="uuid-for-org-3", name="Test Org 3")
    db_session.add(test_org)
    db_session.commit()
    
    # 1. Setup Mocks
    mock_supabase_client.auth.admin.get_user_by_email.return_value = mock_existing_auth_user
    
    # Pre-seed DB with profile AND member link
    profile = Profile(id="uuid-for-existing-auth-user", full_name="Test User")
    member_link = OrganizationMember(
        organization_id="uuid-for-org-3",
        user_id="uuid-for-existing-auth-user",
        role=OrgRole.viewer # <-- Start as viewer
    )
    db_session.add_all([profile, member_link])
    db_session.commit()
    
    with patch('app.services.invitations.supabase', mock_supabase_client):
        service = InvitationService(db_session)
        
        # 2. Run Service
        member = await service.invite_or_add_user_to_org(
            org_id="uuid-for-org-3",
            email=mock_existing_auth_user_email,
            role=OrgRole.member # <-- Upgrade to member
        )
        
        # 3. Assertions
        assert member.user_id == "uuid-for-existing-auth-user"
        assert member.role == OrgRole.member # Role was updated
        
        member_count = db_session.query(OrganizationMember).filter(
            OrganizationMember.user_id == "uuid-for-existing-auth-user"
        ).count()
        assert member_count == 1 # No new record was created
