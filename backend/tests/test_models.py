import pytest
from sqlalchemy import inspect
from app.models import Organization, Profile, OrganizationMember, OrgRole, MemberStatus

def test_organization_model():
    inspector = inspect(Organization)
    columns = [c.name for c in inspector.columns]
    assert 'id' in columns
    assert 'name' in columns
    assert 'created_at' in columns
    
    # Check relationships
    relationships = [r.key for r in inspector.relationships]
    assert 'members' in relationships

def test_profile_model():
    inspector = inspect(Profile)
    columns = [c.name for c in inspector.columns]
    assert 'id' in columns
    assert 'full_name' in columns
    
    # Check relationships
    relationships = [r.key for r in inspector.relationships]
    assert 'memberships' in relationships

def test_organization_member_model():
    inspector = inspect(OrganizationMember)
    columns = [c.name for c in inspector.columns]
    assert 'id' in columns
    assert 'organization_id' in columns
    assert 'user_id' in columns
    assert 'role' in columns
    assert 'status' in columns
    assert 'joined_at' in columns
    
    # Check enums
    assert inspector.columns['role'].type.enums == [e.value for e in OrgRole]
    assert inspector.columns['status'].type.enums == [e.value for e in MemberStatus]
    
    # Check relationships
    relationships = [r.key for r in inspector.relationships]
    assert 'organization' in relationships
    assert 'user_profile' in relationships
