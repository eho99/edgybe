import pytest
import uuid
from datetime import datetime
from app.schemas import (
    Organization, OrganizationCreate, UserInvite, SupabaseUser, 
    AuthenticatedMember, OrganizationMembership
)
from app.models import OrgRole

def test_organization_schema():
    # Test valid data
    org_data = {"id": uuid.uuid4(), "name": "Test Org", "created_at": datetime.now()}
    org = Organization(**org_data)
    assert org.name == "Test Org"

    # Test create schema
    org_create_data = {"name": "New Org"}
    org_create = OrganizationCreate(**org_create_data)
    assert org_create.name == "New Org"

def test_user_invite_schema():
    invite_data = {"email": "test@example.com", "role": OrgRole.member}
    invite = UserInvite(**invite_data)
    assert invite.email == "test@example.com"
    assert invite.role == OrgRole.member

def test_supabase_user_schema():
    user_data = {"id": uuid.uuid4(), "email": "supabase@example.com"}
    user = SupabaseUser(**user_data)
    assert user.email == "supabase@example.com"

def test_authenticated_member_schema():
    user_data = {"id": uuid.uuid4(), "email": "auth@example.com"}
    auth_member_data = {
        "user": user_data,
        "org_id": uuid.uuid4(),
        "role": OrgRole.admin
    }
    auth_member = AuthenticatedMember(**auth_member_data)
    assert auth_member.role == OrgRole.admin
    assert auth_member.user.email == "auth@example.com"

def test_organization_membership_schema():
    membership_data = {
        "org_id": uuid.uuid4(),
        "role": OrgRole.viewer,
        "organization_name": "Test Org",
        "joined_at": datetime.now()
    }
    membership = OrganizationMembership(**membership_data)
    assert membership.organization_name == "Test Org"
    assert membership.role == OrgRole.viewer
