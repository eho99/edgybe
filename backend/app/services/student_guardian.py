from uuid import UUID
import uuid
import logging
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from .. import models, schemas

logger = logging.getLogger(__name__)

class StudentGuardianService:
    def __init__(self, db: Session):
        self.db = db

    def get_link_by_ids(self, org_id: UUID, student_id: UUID, guardian_id: UUID):
        return self.db.query(models.StudentGuardian).filter(
        models.StudentGuardian.organization_id == org_id,
        models.StudentGuardian.guardian_id == guardian_id,
        models.StudentGuardian.student_id == student_id
    ).first()

    def create_guardian_link(self, org_id: UUID, link_data: schemas.GuardianLinkRequest) -> models.StudentGuardian:
        # 1. Prevent self-guardianship
        if link_data.guardian_id == link_data.student_id:
            raise HTTPException(status_code=400, detail="A student cannot be their own guardian")
        
        # 2. Validation: Ensure both users exist in the Org
        guardian_member = self.db.query(models.OrganizationMember).filter_by(
            user_id=link_data.guardian_id, organization_id=org_id
        ).first()
        
        student_member = self.db.query(models.OrganizationMember).filter_by(
            user_id=link_data.student_id, organization_id=org_id
        ).first()

        if not guardian_member:
            raise HTTPException(status_code=404, detail="Guardian not found in this organization")
        if not student_member:
            raise HTTPException(status_code=404, detail="Student not found in this organization")

        # 3. Role validation: Guardian must have guardian role
        if guardian_member.role != models.OrgRole.guardian:
            raise HTTPException(
                status_code=400, 
                detail=f"User with role '{guardian_member.role.value}' cannot be linked as a guardian. Only users with 'guardian' role can be guardians."
            )
        
        # 4. Role validation: Student must have student role
        if student_member.role != models.OrgRole.student:
            raise HTTPException(
                status_code=400,
                detail=f"User with role '{student_member.role.value}' cannot be linked as a student. Only users with 'student' role can be students."
            )

        # 5. Check for duplicates
        if self.get_link_by_ids(org_id, link_data.student_id, link_data.guardian_id):
            raise HTTPException(status_code=400, detail="Relationship already exists")

        # 6. Create
        new_link = models.StudentGuardian(
            organization_id=org_id,
            guardian_id=link_data.guardian_id,
            student_id=link_data.student_id,
            relationship_type=link_data.relationship_type
        )
        self.db.add(new_link)
        self.db.commit()
        self.db.refresh(new_link)
        
        # Eagerly load relationships for response
        new_link = self.db.query(models.StudentGuardian).options(
            joinedload(models.StudentGuardian.student),
            joinedload(models.StudentGuardian.guardian)
        ).filter(models.StudentGuardian.id == new_link.id).first()
        
        return new_link

    def get_guardians_for_student(self, org_id: UUID, student_id: UUID):
        # Verify student exists first (optional, but good for 404 accuracy)
        student = self.db.query(models.Profile).filter(models.Profile.id == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        # Return the ORM objects directly. Pydantic will handle the conversion.
        return self.db.query(models.StudentGuardian).options(
            joinedload(models.StudentGuardian.student),
            joinedload(models.StudentGuardian.guardian)
        ).filter(
            models.StudentGuardian.organization_id == org_id,
            models.StudentGuardian.student_id == student_id
        ).all()

    def get_students_for_guardian(self, org_id: UUID, guardian_id: UUID):
        guardian = self.db.query(models.Profile).filter(models.Profile.id == guardian_id).first()
        if not guardian:
            raise HTTPException(status_code=404, detail="Guardian not found")

        return self.db.query(models.StudentGuardian).options(
            joinedload(models.StudentGuardian.student),
            joinedload(models.StudentGuardian.guardian)
        ).filter(
            models.StudentGuardian.organization_id == org_id,
            models.StudentGuardian.guardian_id == guardian_id
        ).all()

    def delete_guardian_link(self, org_id: UUID, guardian_id: UUID, student_id: UUID):
        link = self.get_link_by_ids(org_id, student_id, guardian_id)
        if not link:
            raise HTTPException(status_code=404, detail="Relationship not found")
        
        self.db.delete(link)
        self.db.commit()

    def create_student_profile(
        self,
        org_id: UUID,
        full_name: str,
        email: str | None = None,
        profile_id: UUID | None = None
    ) -> tuple[models.Profile, models.OrganizationMember]:
        """
        Creates a student profile and organization membership.
        No Supabase Auth account is created - this is just a data record.
        
        Args:
            org_id: Organization ID
            full_name: Student's full name
            email: Optional email (for contact info, not for login)
            profile_id: Optional UUID (auto-generated if not provided)
            
        Returns:
            Tuple of (Profile, OrganizationMember)
        """
        # Generate UUID if not provided
        if not profile_id:
            profile_id = uuid.uuid4()
        
        # Check if profile already exists
        existing_profile = self.db.query(models.Profile).filter(
            models.Profile.id == profile_id
        ).first()
        
        if existing_profile:
            raise HTTPException(
                status_code=400,
                detail=f"Profile with ID {profile_id} already exists"
            )
        
        # Create profile
        profile = models.Profile(
            id=profile_id,
            full_name=full_name,
            has_completed_profile=False  # Not applicable for non-auth profiles
        )
        self.db.add(profile)
        
        # Check if organization membership already exists
        existing_member = self.db.query(models.OrganizationMember).filter(
            models.OrganizationMember.organization_id == org_id,
            models.OrganizationMember.user_id == profile_id
        ).first()
        
        if existing_member:
            raise HTTPException(
                status_code=400,
                detail="Student is already a member of this organization"
            )
        
        # Create organization membership
        member = models.OrganizationMember(
            organization_id=org_id,
            user_id=profile_id,  # Link to profile, even though no auth user exists
            role=models.OrgRole.student,
            status=models.MemberStatus.inactive  # Auto-set by __init__
        )
        self.db.add(member)
        
        self.db.commit()
        self.db.refresh(profile)
        self.db.refresh(member)
        
        return profile, member
    
    def create_guardian_profile(
        self,
        org_id: UUID,
        full_name: str,
        email: str | None = None,
        profile_id: UUID | None = None
    ) -> tuple[models.Profile, models.OrganizationMember]:
        """
        Creates a guardian profile and organization membership.
        No Supabase Auth account is created - this is just a data record.
        
        Args:
            org_id: Organization ID
            full_name: Guardian's full name
            email: Optional email (for contact info, not for login)
            profile_id: Optional UUID (auto-generated if not provided)
            
        Returns:
            Tuple of (Profile, OrganizationMember)
        """
        if not profile_id:
            profile_id = uuid.uuid4()
        
        # Check if profile already exists
        existing_profile = self.db.query(models.Profile).filter(
            models.Profile.id == profile_id
        ).first()
        
        if existing_profile:
            raise HTTPException(
                status_code=400,
                detail=f"Profile with ID {profile_id} already exists"
            )
        
        profile = models.Profile(
            id=profile_id,
            full_name=full_name,
            has_completed_profile=False
        )
        self.db.add(profile)
        
        # Check if organization membership already exists
        existing_member = self.db.query(models.OrganizationMember).filter(
            models.OrganizationMember.organization_id == org_id,
            models.OrganizationMember.user_id == profile_id
        ).first()
        
        if existing_member:
            raise HTTPException(
                status_code=400,
                detail="Guardian is already a member of this organization"
            )
        
        member = models.OrganizationMember(
            organization_id=org_id,
            user_id=profile_id,
            role=models.OrgRole.guardian,
            status=models.MemberStatus.inactive
        )
        self.db.add(member)
        
        self.db.commit()
        self.db.refresh(profile)
        self.db.refresh(member)
        
        return profile, member
    
    def bulk_create_students(
        self,
        org_id: UUID,
        students: list[schemas.StudentData]
    ) -> list[tuple[models.Profile, models.OrganizationMember]]:
        """
        Bulk create student profiles.
        
        Args:
            org_id: Organization ID
            students: List of StudentData objects
            
        Returns:
            List of (Profile, OrganizationMember) tuples
        """
        results = []
        errors = []
        
        for idx, student_data in enumerate(students):
            try:
                profile, member = self.create_student_profile(
                    org_id=org_id,
                    full_name=student_data.full_name,
                    email=student_data.email
                )
                results.append((profile, member))
            except Exception as e:
                errors.append({
                    "index": idx,
                    "data": student_data.dict(),
                    "error": str(e)
                })
                logger.warning(f"Failed to create student at index {idx}: {e}")
        
        if errors and not results:
            # If all failed, raise an error
            raise HTTPException(
                status_code=400,
                detail=f"Failed to create any students. Errors: {errors}"
            )
        
        return results
    
    def bulk_create_guardians(
        self,
        org_id: UUID,
        guardians: list[schemas.GuardianData]
    ) -> list[tuple[models.Profile, models.OrganizationMember]]:
        """Bulk create guardian profiles."""
        results = []
        errors = []
        
        for idx, guardian_data in enumerate(guardians):
            try:
                profile, member = self.create_guardian_profile(
                    org_id=org_id,
                    full_name=guardian_data.full_name,
                    email=guardian_data.email
                )
                results.append((profile, member))
            except Exception as e:
                errors.append({
                    "index": idx,
                    "data": guardian_data.dict(),
                    "error": str(e)
                })
                logger.warning(f"Failed to create guardian at index {idx}: {e}")
        
        if errors and not results:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to create any guardians. Errors: {errors}"
            )
        
        return results
    
    def bulk_create_and_link(
        self,
        org_id: UUID,
        pairs: list[schemas.StudentGuardianPair]
    ) -> list[dict]:
        """
        Bulk create student-guardian pairs and link them.
        
        Args:
            org_id: Organization ID
            pairs: List of StudentGuardianPair objects
                
        Returns:
            List of result dicts with 'student_profile', 'guardian_profile', 'link'
        """
        results = []
        errors = []
        
        for idx, pair_data in enumerate(pairs):
            try:
                # Create student
                student_profile, student_member = self.create_student_profile(
                    org_id=org_id,
                    full_name=pair_data.student.full_name,
                    email=pair_data.student.email
                )
                
                # Create guardian
                guardian_profile, guardian_member = self.create_guardian_profile(
                    org_id=org_id,
                    full_name=pair_data.guardian.full_name,
                    email=pair_data.guardian.email
                )
                
                # Link them
                link_data = schemas.GuardianLinkRequest(
                    guardian_id=guardian_profile.id,
                    student_id=student_profile.id,
                    relationship_type=pair_data.relationship_type
                )
                
                try:
                    link = self.create_guardian_link(org_id, link_data)
                    # Convert link to dict for serialization
                    link_dict = {
                        "id": str(link.id),
                        "organization_id": str(link.organization_id),
                        "student_id": str(link.student_id),
                        "guardian_id": str(link.guardian_id),
                        "relationship_type": link.relationship_type.value,
                        "student": {
                            "id": str(link.student.id),
                            "full_name": link.student.full_name,
                            "has_completed_profile": link.student.has_completed_profile or False
                        },
                        "guardian": {
                            "id": str(link.guardian.id),
                            "full_name": link.guardian.full_name,
                            "has_completed_profile": link.guardian.has_completed_profile or False
                        }
                    }
                except HTTPException as e:
                    # Shouldn't happen, but handle gracefully
                    logger.warning(f"Failed to create link for pair {idx}: {e.detail}")
                    link_dict = None
                
                results.append({
                    "student_profile": {
                        "id": str(student_profile.id),
                        "full_name": student_profile.full_name,
                        "has_completed_profile": student_profile.has_completed_profile or False
                    },
                    "guardian_profile": {
                        "id": str(guardian_profile.id),
                        "full_name": guardian_profile.full_name,
                        "has_completed_profile": guardian_profile.has_completed_profile or False
                    },
                    "link": link_dict
                })
            except Exception as e:
                errors.append({
                    "index": idx,
                    "data": pair_data.dict(),
                    "error": str(e)
                })
                logger.warning(f"Failed to create pair at index {idx}: {e}")
        
        if errors and not results:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to create any pairs. Errors: {errors}"
            )
        
        return results