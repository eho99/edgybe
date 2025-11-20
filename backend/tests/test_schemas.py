from pydantic_extra_types.phone_numbers import PhoneNumber
import pytest
import uuid
from datetime import datetime
from pydantic import ValidationError
from app.schemas import (
    Organization, OrganizationCreate, OrganizationUpdate, UserInvite, SupabaseUser, 
    AuthenticatedMember, OrganizationMembership, ProfileSchema, ProfileUpdateSchema
)
from app.models import OrgRole

def test_organization_schema():
    # Test valid data with minimal fields
    org_data = {
        "id": uuid.uuid4(), 
        "name": "Test Org", 
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    org = Organization(**org_data)
    assert org.name == "Test Org"

    # Test create schema with new fields
    org_create_data = {
        "name": "New Org",
        "street_number": "123",
        "street_name": "Main St",
        "city": "Springfield",
        "state": "IL",
        "zip_code": "62701",
        "phone_number": "+14155552671",
        "lower_grade": 0,
        "upper_grade": 12,
        "slug": "new-org",
        "disclaimers": {"privacy": "We respect your privacy", "terms": "By using this service..."}
    }
    org_create = OrganizationCreate(**org_create_data)
    assert org_create.name == "New Org"
    assert org_create.city == "Springfield"
    assert org_create.lower_grade == 0
    assert org_create.upper_grade == 12
    assert org_create.disclaimers == {"privacy": "We respect your privacy", "terms": "By using this service..."}

def test_phone_validation():
    """Test phone number validation in organization schema."""
    # Valid phone numbers - PhoneNumber may normalize the format
    valid_phones = [
        "+19494380223",
        "+1 (949) 438-0223",
        "+1 949 438 0223",
        "+1 949-438-0223",
    ]
    
    for phone in valid_phones:
        org_data = {
            "name": "Test Org",
            "phone_number": phone
        }
        org = OrganizationCreate(**org_data)
        # PhoneNumber validates and may normalize, so just check it's not None
        assert org.phone_number is not None
    
    # Invalid phone numbers
    invalid_phones = ["123", "abc", "(949) 438-0223"]
    
    for phone in invalid_phones:
        # pydantic-extra-types raises ValidationError for invalid phone numbers
        with pytest.raises(ValidationError):
            OrganizationCreate(name="Test Org", phone_number=phone)

def test_organization_grade_range_validation():
    """Test grade range validation."""
    # Valid range
    org = OrganizationCreate(name="Test Org", lower_grade=0, upper_grade=12)
    assert org.lower_grade == 0
    assert org.upper_grade == 12
    
    # Invalid range (lower > upper)
    with pytest.raises(ValueError, match="lower_grade must be less than or equal"):
        OrganizationCreate(name="Test Org", lower_grade=12, upper_grade=0)
    
    # Valid single grade
    org = OrganizationCreate(name="Test Org", lower_grade=9, upper_grade=9)
    assert org.lower_grade == 9
    assert org.upper_grade == 9

def test_organization_update_schema():
    """Test that OrganizationUpdate allows partial updates."""
    # All fields optional
    update_data = {"name": "Updated Name"}
    org_update = OrganizationUpdate(**update_data)
    assert org_update.name == "Updated Name"
    
    # Can update just phone
    update_data = {"phone_number": "+19494380223"}
    org_update = OrganizationUpdate(**update_data)
    assert org_update.phone_number is not None
    assert isinstance(org_update.phone_number, str)

def test_user_invite_schema():
    invite_data = {"email": "test@example.com", "role": OrgRole.staff}
    invite = UserInvite(**invite_data)
    assert invite.email == "test@example.com"
    assert invite.role == OrgRole.staff

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
        "role": OrgRole.student,
        "organization_name": "Test Org",
        "joined_at": datetime.now()
    }
    membership = OrganizationMembership(**membership_data)
    assert membership.organization_name == "Test Org"
    assert membership.role == OrgRole.student

def test_all_role_types():
    """Test that all new role types can be used in schemas."""
    roles = [OrgRole.admin, OrgRole.secretary, OrgRole.staff, OrgRole.guardian, OrgRole.student]
    
    for role in roles:
        membership_data = {
            "org_id": uuid.uuid4(),
            "role": role,
            "organization_name": f"Test Org {role.value}",
            "joined_at": datetime.now()
        }
        membership = OrganizationMembership(**membership_data)
        assert membership.role == role

def test_profile_schema():
    """Test ProfileSchema with new fields."""
    profile_data = {
        "id": uuid.uuid4(),
        "full_name": "John Doe",
        "has_completed_profile": True,
        "phone": "+19494380223",
        "city": "Springfield",
        "state": "IL",
        "preferred_language": "en",
        "grade_level": "9",
        "student_id": "STU123",
        "is_active": True,
        "updated_at": datetime.now()
    }
    profile = ProfileSchema(**profile_data)
    assert profile.full_name == "John Doe"
    assert profile.phone == "tel:+1-949-438-0223"
    assert profile.grade_level == "9"
    assert profile.student_id == "STU123"
    assert profile.is_active == True


def test_profile_update_schema():
    """Test ProfileUpdateSchema allows partial updates."""
    # All fields optional
    update_data = {"full_name": "Updated Name"}
    profile_update = ProfileUpdateSchema(**update_data)
    assert profile_update.full_name == "Updated Name"
    
    # Can update just phone
    update_data = {"phone": "+19494380223"}
    profile_update = ProfileUpdateSchema(**update_data)
    assert profile_update.phone == "tel:+1-949-438-0223"
    
    # Can update student fields
    update_data = {"grade_level": "10", "student_id": "STU456"}
    profile_update = ProfileUpdateSchema(**update_data)
    assert profile_update.grade_level == "10"
    assert profile_update.student_id == "STU456"
