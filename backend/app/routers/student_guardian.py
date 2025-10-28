from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import UUID4
from sqlalchemy.orm import Session

from .. import models, schemas, auth
from ..db import get_db

router = APIRouter(
    prefix="/api/v1/organizations/{org_id}",
    tags=["Student-Guardian Relationships"],
)

@router.post(
    "/guardians/link",
    response_model=schemas.GuardianLinkResponse
)
async def link_guardian_to_student(
    org_id: UUID4,
    link_request: schemas.GuardianLinkRequest,
    db: Session = Depends(get_db),
    admin_member: schemas.AuthenticatedMember = Depends(auth.require_admin_role)
):
    """
    Creates a relationship between a guardian and student within an organization.
    Only Admins can perform this action.
    """
    # Check if both users exist in the organization
    guardian_member = db.query(models.OrganizationMember).filter(
        models.OrganizationMember.user_id == link_request.guardian_id,
        models.OrganizationMember.organization_id == org_id
    ).first()
    
    student_member = db.query(models.OrganizationMember).filter(
        models.OrganizationMember.user_id == link_request.student_id,
        models.OrganizationMember.organization_id == org_id
    ).first()
    
    if not guardian_member:
        raise HTTPException(status_code=404, detail="Guardian not found in this organization")
    
    if not student_member:
        raise HTTPException(status_code=404, detail="Student not found in this organization")
    
    # Check if relationship already exists
    existing_link = db.query(models.StudentGuardian).filter(
        models.StudentGuardian.organization_id == org_id,
        models.StudentGuardian.guardian_id == link_request.guardian_id,
        models.StudentGuardian.student_id == link_request.student_id
    ).first()
    
    if existing_link:
        raise HTTPException(status_code=400, detail="Relationship already exists")
    
    # Create the relationship
    student_guardian = models.StudentGuardian(
        organization_id=org_id,
        guardian_id=link_request.guardian_id,
        student_id=link_request.student_id,
        relationship_type=link_request.relationship_type
    )
    
    db.add(student_guardian)
    db.commit()
    db.refresh(student_guardian)
    
    return student_guardian

@router.get(
    "/students/{student_id}/guardians",
    response_model=schemas.StudentWithGuardiansResponse
)
async def get_student_guardians(
    org_id: UUID4,
    student_id: UUID4,
    db: Session = Depends(get_db),
    member: schemas.AuthenticatedMember = Depends(auth.require_any_role)
):
    """
    Gets all guardians for a specific student within an organization.
    """
    # Get student profile
    student_profile = db.query(models.Profile).filter(
        models.Profile.id == student_id
    ).first()
    
    if not student_profile:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get guardian relationships
    guardian_links = db.query(models.StudentGuardian).filter(
        models.StudentGuardian.organization_id == org_id,
        models.StudentGuardian.student_id == student_id
    ).all()
    
    return schemas.StudentWithGuardiansResponse(
        student=student_profile,
        guardians=guardian_links
    )

@router.get(
    "/guardians/{guardian_id}/students",
    response_model=schemas.GuardianWithStudentsResponse
)
async def get_guardian_students(
    org_id: UUID4,
    guardian_id: UUID4,
    db: Session = Depends(get_db),
    member: schemas.AuthenticatedMember = Depends(auth.require_any_role)
):
    """
    Gets all students for a specific guardian within an organization.
    """
    # Get guardian profile
    guardian_profile = db.query(models.Profile).filter(
        models.Profile.id == guardian_id
    ).first()
    
    if not guardian_profile:
        raise HTTPException(status_code=404, detail="Guardian not found")
    
    # Get student relationships
    student_links = db.query(models.StudentGuardian).filter(
        models.StudentGuardian.organization_id == org_id,
        models.StudentGuardian.guardian_id == guardian_id
    ).all()
    
    return schemas.GuardianWithStudentsResponse(
        guardian=guardian_profile,
        students=student_links
    )

@router.delete(
    "/guardians/link"
)
async def unlink_guardian_from_student(
    org_id: UUID4,
    guardian_id: UUID4 = Query(...),
    student_id: UUID4 = Query(...),
    db: Session = Depends(get_db),
    admin_member: schemas.AuthenticatedMember = Depends(auth.require_admin_role)
):
    """
    Removes a relationship between a guardian and student within an organization.
    Only Admins can perform this action.
    """
    # Find the relationship
    student_guardian = db.query(models.StudentGuardian).filter(
        models.StudentGuardian.organization_id == org_id,
        models.StudentGuardian.guardian_id == guardian_id,
        models.StudentGuardian.student_id == student_id
    ).first()
    
    if not student_guardian:
        raise HTTPException(status_code=404, detail="Relationship not found")
    
    db.delete(student_guardian)
    db.commit()
    
    return {"message": "Relationship removed successfully"}
