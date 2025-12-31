"""
Tests for admin assignment logic in referral creation.
Tests assignment by grade and alphabetical order.
"""
import pytest
import uuid
from sqlalchemy.orm import Session

from app.models import (
    Profile, Organization, OrganizationMember,
    Referral, OrgRole, MemberStatus
)
from app.services import referral_service


@pytest.fixture
def test_org(db_session):
    """Create a test organization."""
    org = Organization(
        id=uuid.uuid4(),
        name="Test School",
        phone_number="+14155551234"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture
def admin_profile_1(db_session, test_org):
    """Create first admin profile."""
    admin_id = uuid.uuid4()
    profile = Profile(
        id=admin_id,
        full_name="Admin One",
        email="admin1@test.com",
        is_active=True
    )
    db_session.add(profile)
    
    member = OrganizationMember(
        organization_id=test_org.id,
        user_id=admin_id,
        role=OrgRole.admin,
        status=MemberStatus.active
    )
    db_session.add(member)
    db_session.commit()
    db_session.refresh(profile)
    return profile


@pytest.fixture
def admin_profile_2(db_session, test_org):
    """Create second admin profile."""
    admin_id = uuid.uuid4()
    profile = Profile(
        id=admin_id,
        full_name="Admin Two",
        email="admin2@test.com",
        is_active=True
    )
    db_session.add(profile)
    
    member = OrganizationMember(
        organization_id=test_org.id,
        user_id=admin_id,
        role=OrgRole.admin,
        status=MemberStatus.active
    )
    db_session.add(member)
    db_session.commit()
    db_session.refresh(profile)
    return profile


@pytest.fixture
def admin_profile_3(db_session, test_org):
    """Create third admin profile."""
    admin_id = uuid.uuid4()
    profile = Profile(
        id=admin_id,
        full_name="Admin Three",
        email="admin3@test.com",
        is_active=True
    )
    db_session.add(profile)
    
    member = OrganizationMember(
        organization_id=test_org.id,
        user_id=admin_id,
        role=OrgRole.admin,
        status=MemberStatus.active
    )
    db_session.add(member)
    db_session.commit()
    db_session.refresh(profile)
    return profile


class TestAssignmentByGrade:
    """Tests for grade-based assignment."""
    
    def test_assign_by_grade_exact_match(self, db_session, test_org, admin_profile_1, admin_profile_2):
        """Test assignment when student grade matches exactly."""
        # Configure assignment by grade
        test_org.assignment_config = {
            "type": "grade",
            "grade_mappings": {
                "9": str(admin_profile_1.id),
                "10": str(admin_profile_2.id),
                "11": str(admin_profile_1.id),
                "12": str(admin_profile_2.id)
            }
        }
        db_session.commit()
        
        # Create student with grade 9
        student = Profile(
            id=uuid.uuid4(),
            full_name="Student One",
            grade_level="9",
            is_active=True
        )
        db_session.add(student)
        db_session.commit()
        
        # Assign admin
        assigned_id = referral_service.assign_admin_to_referral(
            db=db_session,
            organization=test_org,
            student=student
        )
        
        assert assigned_id == admin_profile_1.id
    
    def test_assign_by_grade_numeric_match(self, db_session, test_org, admin_profile_1, admin_profile_2):
        """Test assignment when student grade is numeric string."""
        # Configure assignment by grade
        test_org.assignment_config = {
            "type": "grade",
            "grade_mappings": {
                "9": str(admin_profile_1.id),
                "10": str(admin_profile_2.id)
            }
        }
        db_session.commit()
        
        # Create student with numeric grade
        student = Profile(
            id=uuid.uuid4(),
            full_name="Student Two",
            grade_level=9,  # Numeric, not string
            is_active=True
        )
        db_session.add(student)
        db_session.commit()
        
        # Assign admin
        assigned_id = referral_service.assign_admin_to_referral(
            db=db_session,
            organization=test_org,
            student=student
        )
        
        assert assigned_id == admin_profile_1.id
    
    def test_assign_by_grade_no_match(self, db_session, test_org, admin_profile_1):
        """Test assignment when student grade doesn't match any mapping."""
        # Configure assignment by grade
        test_org.assignment_config = {
            "type": "grade",
            "grade_mappings": {
                "9": str(admin_profile_1.id),
                "10": str(admin_profile_1.id)
            }
        }
        db_session.commit()
        
        # Create student with grade 11 (not in mappings)
        student = Profile(
            id=uuid.uuid4(),
            full_name="Student Three",
            grade_level="11",
            is_active=True
        )
        db_session.add(student)
        db_session.commit()
        
        # Assign admin
        assigned_id = referral_service.assign_admin_to_referral(
            db=db_session,
            organization=test_org,
            student=student
        )
        
        assert assigned_id is None
    
    def test_assign_by_grade_no_grade_level(self, db_session, test_org, admin_profile_1):
        """Test assignment when student has no grade level."""
        # Configure assignment by grade
        test_org.assignment_config = {
            "type": "grade",
            "grade_mappings": {
                "9": str(admin_profile_1.id)
            }
        }
        db_session.commit()
        
        # Create student without grade
        student = Profile(
            id=uuid.uuid4(),
            full_name="Student Four",
            is_active=True
        )
        db_session.add(student)
        db_session.commit()
        
        # Assign admin
        assigned_id = referral_service.assign_admin_to_referral(
            db=db_session,
            organization=test_org,
            student=student
        )
        
        assert assigned_id is None


class TestAssignmentByAlphabetical:
    """Tests for alphabetical assignment."""
    
    def test_assign_by_last_name_single_letter(self, db_session, test_org, admin_profile_1, admin_profile_2):
        """Test assignment by last name with single letter ranges."""
        # Configure assignment by alphabetical (last name)
        test_org.assignment_config = {
            "type": "alphabetical",
            "name_field": "last_name",
            "letter_ranges": {
                "A-M": str(admin_profile_1.id),
                "N-Z": str(admin_profile_2.id)
            }
        }
        db_session.commit()
        
        # Create student with last name starting with A
        student = Profile(
            id=uuid.uuid4(),
            full_name="John Anderson",
            is_active=True
        )
        db_session.add(student)
        db_session.commit()
        
        # Assign admin
        assigned_id = referral_service.assign_admin_to_referral(
            db=db_session,
            organization=test_org,
            student=student
        )
        
        assert assigned_id == admin_profile_1.id
    
    def test_assign_by_last_name_range(self, db_session, test_org, admin_profile_1, admin_profile_2, admin_profile_3):
        """Test assignment by last name with letter ranges."""
        # Configure assignment by alphabetical
        test_org.assignment_config = {
            "type": "alphabetical",
            "name_field": "last_name",
            "letter_ranges": {
                "A-F": str(admin_profile_1.id),
                "G-M": str(admin_profile_2.id),
                "N-Z": str(admin_profile_3.id)
            }
        }
        db_session.commit()
        
        # Create student with last name starting with G
        student = Profile(
            id=uuid.uuid4(),
            full_name="Jane Garcia",
            is_active=True
        )
        db_session.add(student)
        db_session.commit()
        
        # Assign admin
        assigned_id = referral_service.assign_admin_to_referral(
            db=db_session,
            organization=test_org,
            student=student
        )
        
        assert assigned_id == admin_profile_2.id
    
    def test_assign_by_first_name(self, db_session, test_org, admin_profile_1, admin_profile_2):
        """Test assignment by first name."""
        # Configure assignment by first name
        test_org.assignment_config = {
            "type": "alphabetical",
            "name_field": "first_name",
            "letter_ranges": {
                "A-M": str(admin_profile_1.id),
                "N-Z": str(admin_profile_2.id)
            }
        }
        db_session.commit()
        
        # Create student with first name starting with N
        student = Profile(
            id=uuid.uuid4(),
            full_name="Nancy Smith",
            is_active=True
        )
        db_session.add(student)
        db_session.commit()
        
        # Assign admin
        assigned_id = referral_service.assign_admin_to_referral(
            db=db_session,
            organization=test_org,
            student=student
        )
        
        assert assigned_id == admin_profile_2.id
    
    def test_assign_by_alphabetical_no_match(self, db_session, test_org, admin_profile_1):
        """Test assignment when name doesn't match any range."""
        # Configure assignment by alphabetical
        test_org.assignment_config = {
            "type": "alphabetical",
            "name_field": "last_name",
            "letter_ranges": {
                "A-M": str(admin_profile_1.id)
            }
        }
        db_session.commit()
        
        # Create student with last name starting with Z (not in range)
        student = Profile(
            id=uuid.uuid4(),
            full_name="John Zulu",
            is_active=True
        )
        db_session.add(student)
        db_session.commit()
        
        # Assign admin
        assigned_id = referral_service.assign_admin_to_referral(
            db=db_session,
            organization=test_org,
            student=student
        )
        
        assert assigned_id is None
    
    def test_assign_by_alphabetical_no_name(self, db_session, test_org, admin_profile_1):
        """Test assignment when student has no name."""
        # Configure assignment by alphabetical
        test_org.assignment_config = {
            "type": "alphabetical",
            "name_field": "last_name",
            "letter_ranges": {
                "A-Z": str(admin_profile_1.id)
            }
        }
        db_session.commit()
        
        # Create student without name
        student = Profile(
            id=uuid.uuid4(),
            is_active=True
        )
        db_session.add(student)
        db_session.commit()
        
        # Assign admin
        assigned_id = referral_service.assign_admin_to_referral(
            db=db_session,
            organization=test_org,
            student=student
        )
        
        assert assigned_id is None


class TestAssignmentEdgeCases:
    """Tests for edge cases in assignment logic."""
    
    def test_no_assignment_config(self, db_session, test_org, admin_profile_1):
        """Test when organization has no assignment config."""
        test_org.assignment_config = None
        db_session.commit()
        
        student = Profile(
            id=uuid.uuid4(),
            full_name="Student One",
            grade_level="9",
            is_active=True
        )
        db_session.add(student)
        db_session.commit()
        
        assigned_id = referral_service.assign_admin_to_referral(
            db=db_session,
            organization=test_org,
            student=student
        )
        
        assert assigned_id is None
    
    def test_invalid_assignment_type(self, db_session, test_org, admin_profile_1):
        """Test when assignment type is invalid."""
        test_org.assignment_config = {
            "type": "invalid_type",
            "grade_mappings": {
                "9": str(admin_profile_1.id)
            }
        }
        db_session.commit()
        
        student = Profile(
            id=uuid.uuid4(),
            full_name="Student One",
            grade_level="9",
            is_active=True
        )
        db_session.add(student)
        db_session.commit()
        
        assigned_id = referral_service.assign_admin_to_referral(
            db=db_session,
            organization=test_org,
            student=student
        )
        
        assert assigned_id is None
    
    def test_no_active_admins(self, db_session, test_org):
        """Test when organization has no active admins."""
        test_org.assignment_config = {
            "type": "grade",
            "grade_mappings": {
                "9": str(uuid.uuid4())  # Non-existent admin
            }
        }
        db_session.commit()
        
        student = Profile(
            id=uuid.uuid4(),
            full_name="Student One",
            grade_level="9",
            is_active=True
        )
        db_session.add(student)
        db_session.commit()
        
        assigned_id = referral_service.assign_admin_to_referral(
            db=db_session,
            organization=test_org,
            student=student
        )
        
        assert assigned_id is None
    
    def test_admin_not_in_organization(self, db_session, test_org, admin_profile_1):
        """Test when mapped admin is not in the organization."""
        # Create admin in different org
        other_org = Organization(
            id=uuid.uuid4(),
            name="Other School"
        )
        db_session.add(other_org)
        db_session.commit()
        
        test_org.assignment_config = {
            "type": "grade",
            "grade_mappings": {
                "9": str(admin_profile_1.id)
            }
        }
        db_session.commit()
        
        # Remove admin from test_org
        db_session.query(OrganizationMember).filter(
            OrganizationMember.organization_id == test_org.id,
            OrganizationMember.user_id == admin_profile_1.id
        ).delete()
        db_session.commit()
        
        student = Profile(
            id=uuid.uuid4(),
            full_name="Student One",
            grade_level="9",
            is_active=True
        )
        db_session.add(student)
        db_session.commit()
        
        assigned_id = referral_service.assign_admin_to_referral(
            db=db_session,
            organization=test_org,
            student=student
        )
        
        assert assigned_id is None

