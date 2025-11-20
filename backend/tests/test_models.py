import pytest
from sqlalchemy import inspect
from app.models import (
    Organization,
    District,
    Profile,
    OrganizationMember,
    OrgRole,
    MemberStatus,
)

def test_organization_model():
    inspector = inspect(Organization)
    columns = [c.name for c in inspector.columns]
    assert 'id' in columns
    assert 'name' in columns
    assert 'created_at' in columns
    assert 'updated_at' in columns
    
    # Check new address fields
    assert 'district_id' in columns
    assert 'street_number' in columns
    assert 'street_name' in columns
    assert 'city' in columns
    assert 'state' in columns
    assert 'zip_code' in columns
    
    # Check contact fields
    assert 'phone_number' in columns
    assert 'office_extension' in columns
    
    # Check grade fields
    assert 'lower_grade' in columns
    assert 'upper_grade' in columns
    
    # Check other fields
    assert 'slug' in columns
    assert 'preset_config' in columns
    assert 'form_config' in columns
    assert 'aeries_school_code' in columns
    assert 'sis_source_id' in columns
    assert 'sis_client_id' in columns
    assert 'sis_client_secret' in columns
    assert 'disclaimers' in columns
    
    # Check relationships
    relationships = [r.key for r in inspector.relationships]
    assert 'members' in relationships
    assert 'district' in relationships


def test_organization_has_district_relationship(db_session):
    district = District(name="District One")
    db_session.add(district)
    db_session.commit()

    organization = Organization(name="Org With District", district_id=district.id)
    db_session.add(organization)
    db_session.commit()
    db_session.refresh(organization)
    db_session.refresh(district)

    assert organization.district.id == district.id
    assert organization in district.organizations


def test_organization_district_fk_constraint():
    inspector = inspect(Organization)
    fk_list = list(inspector.columns['district_id'].foreign_keys)

    assert fk_list, "district_id should have a foreign key constraint"
    fk = fk_list[0]
    assert fk.column.table.name == 'districts'
    assert fk.target_fullname == 'districts.id'
    assert fk.ondelete == 'RESTRICT'

def test_profile_model():
    inspector = inspect(Profile)
    columns = [c.name for c in inspector.columns]
    assert 'id' in columns
    assert 'full_name' in columns
    assert 'has_completed_profile' in columns
    assert 'updated_at' in columns
    
    # Check contact fields
    assert 'phone' in columns
    
    # Check address fields
    assert 'street_number' in columns
    assert 'street_name' in columns
    assert 'city' in columns
    assert 'state' in columns
    assert 'zip_code' in columns
    assert 'country' in columns
    
    # Check preference fields
    assert 'preferred_language' in columns
    
    # Check student-specific fields
    assert 'grade_level' in columns
    assert 'student_id' in columns
    
    # Check status fields
    assert 'is_active' in columns
    
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
    
    # Check enums - should include all 5 new roles
    expected_roles = ['admin', 'secretary', 'staff', 'guardian', 'student']
    actual_roles = inspector.columns['role'].type.enums
    assert set(actual_roles) == set(expected_roles)
    
    # Check status enum
    assert inspector.columns['status'].type.enums == [e.value for e in MemberStatus]
    
    # Check relationships
    relationships = [r.key for r in inspector.relationships]
    assert 'organization' in relationships
    assert 'user_profile' in relationships

def test_role_hierarchy():
    """Test the role hierarchy levels."""
    from app.auth import get_role_hierarchy_level
    
    # Test hierarchy levels
    assert get_role_hierarchy_level(OrgRole.student) == 1
    assert get_role_hierarchy_level(OrgRole.guardian) == 2
    assert get_role_hierarchy_level(OrgRole.staff) == 3
    assert get_role_hierarchy_level(OrgRole.secretary) == 4
    assert get_role_hierarchy_level(OrgRole.admin) == 5

def test_active_inactive_roles():
    """Test active/inactive role logic."""
    from app.auth import is_active_role, is_inactive_role
    
    # Test active roles
    assert is_active_role(OrgRole.admin) == True
    assert is_active_role(OrgRole.secretary) == True
    assert is_active_role(OrgRole.staff) == True
    
    # Test inactive roles
    assert is_active_role(OrgRole.guardian) == False
    assert is_active_role(OrgRole.student) == False
    
    # Test inactive role function
    assert is_inactive_role(OrgRole.guardian) == True
    assert is_inactive_role(OrgRole.student) == True
    assert is_inactive_role(OrgRole.admin) == False
    assert is_inactive_role(OrgRole.secretary) == False
    assert is_inactive_role(OrgRole.staff) == False

def test_permission_functions():
    """Test permission checking functions."""
    from app.auth import can_manage_users, can_create_content, can_view_content, role_has_permission
    
    # Test can_manage_users (admin only)
    assert can_manage_users(OrgRole.admin) == True
    assert can_manage_users(OrgRole.secretary) == False
    assert can_manage_users(OrgRole.staff) == False
    assert can_manage_users(OrgRole.guardian) == False
    assert can_manage_users(OrgRole.student) == False
    
    # Test can_create_content (admin, secretary, staff)
    assert can_create_content(OrgRole.admin) == True
    assert can_create_content(OrgRole.secretary) == True
    assert can_create_content(OrgRole.staff) == True
    assert can_create_content(OrgRole.guardian) == False
    assert can_create_content(OrgRole.student) == False
    
    # Test can_view_content (all roles)
    for role in [OrgRole.admin, OrgRole.secretary, OrgRole.staff, OrgRole.guardian, OrgRole.student]:
        assert can_view_content(role) == True
    
    # Test role_has_permission (hierarchy-based)
    assert role_has_permission(OrgRole.admin, OrgRole.secretary) == True
    assert role_has_permission(OrgRole.admin, OrgRole.staff) == True
    assert role_has_permission(OrgRole.admin, OrgRole.guardian) == True
    assert role_has_permission(OrgRole.admin, OrgRole.student) == True
    
    assert role_has_permission(OrgRole.secretary, OrgRole.staff) == True
    assert role_has_permission(OrgRole.secretary, OrgRole.guardian) == True
    assert role_has_permission(OrgRole.secretary, OrgRole.student) == True
    
    assert role_has_permission(OrgRole.staff, OrgRole.guardian) == True
    assert role_has_permission(OrgRole.staff, OrgRole.student) == True
    
    # Test reverse permissions (should be False)
    assert role_has_permission(OrgRole.student, OrgRole.admin) == False
    assert role_has_permission(OrgRole.guardian, OrgRole.secretary) == False
    assert role_has_permission(OrgRole.staff, OrgRole.admin) == False
