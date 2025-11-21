from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import UUID4
from sqlalchemy.orm import Session

from .. import schemas, auth, services, models
from ..db import get_db

router = APIRouter(
    prefix="/api/v1/organizations/{org_id}",
    tags=["Student-Guardian Relationships"],
)

@router.post("/guardians/link", response_model=schemas.GuardianLinkResponse)
async def link_guardian_to_student(
    org_id: UUID4,
    link_request: schemas.GuardianLinkRequest,
    db: Session = Depends(get_db),
    admin_member: schemas.AuthenticatedMember = Depends(auth.require_admin_role)
):
    # The service returns the ORM object. 
    # FastAPI/Pydantic automatically converts it to GuardianLinkResponse
    return services.StudentGuardianService(db).create_guardian_link(org_id, link_request)

@router.get("/students/{student_id}/guardians", response_model=schemas.StudentWithGuardiansResponse)
async def get_student_guardians(
    org_id: UUID4,
    student_id: UUID4,
    db: Session = Depends(get_db),
):
    # We need to fetch the student profile separately to populate the top-level 'student' field
    # in the response model, OR we adjust the schema to structure this differently.
    # For now, let's stick to your schema structure:
    
    student_profile = db.query(models.Profile).filter(models.Profile.id == student_id).first()
    if not student_profile:
        raise HTTPException(status_code=404, detail="Student not found")
    links = services.StudentGuardianService(db).get_guardians_for_student(org_id, student_id)
    
    return {
        "student": student_profile,
        "guardians": links # Pydantic iterates this list and converts each item
    }

@router.get("/guardians/{guardian_id}/students", response_model=schemas.GuardianWithStudentsResponse)
async def get_guardian_students(
    org_id: UUID4,
    guardian_id: UUID4,
    db: Session = Depends(get_db),
):
    guardian_profile = db.query(models.Profile).filter(models.Profile.id == guardian_id).first()
    if not guardian_profile:
        raise HTTPException(status_code=404, detail="Guardian not found")
    links = services.StudentGuardianService(db).get_students_for_guardian(org_id, guardian_id)
    
    return {
        "guardian": guardian_profile,
        "students": links
    }

@router.delete("/guardians/link")
async def unlink_guardian_from_student(
    org_id: UUID4,
    guardian_id: UUID4 = Query(...),
    student_id: UUID4 = Query(...),
    db: Session = Depends(get_db),
    admin_member: schemas.AuthenticatedMember = Depends(auth.require_admin_role)
):
    services.StudentGuardianService(db).delete_guardian_link(org_id, guardian_id, student_id)
    return {"message": "Relationship removed successfully"}

# Profile creation endpoints
@router.post("/students", response_model=schemas.ProfileSchema)
async def create_student(
    org_id: UUID4,
    request: schemas.CreateStudentRequest,
    db: Session = Depends(get_db),
    admin_member: schemas.AuthenticatedMember = Depends(auth.require_admin_role)
):
    """Create a single student profile (no auth account)."""
    service = services.StudentGuardianService(db)
    profile, member = service.create_student_profile(
        org_id=org_id,
        full_name=request.full_name,
        grade_level=request.grade_level,
        student_id=request.student_id,
        email=request.email,
        phone=request.phone,
        street_number=request.street_number,
        street_name=request.street_name,
        city=request.city,
        state=request.state,
        zip_code=request.zip_code,
        country=request.country,
        preferred_language=request.preferred_language
    )
    return profile

@router.post("/guardians", response_model=schemas.ProfileSchema)
async def create_guardian(
    org_id: UUID4,
    request: schemas.CreateGuardianRequest,
    db: Session = Depends(get_db),
    admin_member: schemas.AuthenticatedMember = Depends(auth.require_admin_role)
):
    """Create a single guardian profile (no auth account)."""
    service = services.StudentGuardianService(db)
    profile, member = service.create_guardian_profile(
        org_id=org_id,
        full_name=request.full_name,
        email=request.email,
        phone=request.phone,
        street_number=request.street_number,
        street_name=request.street_name,
        city=request.city,
        state=request.state,
        zip_code=request.zip_code,
        country=request.country,
        preferred_language=request.preferred_language
    )
    return profile

@router.post("/students/bulk", response_model=schemas.BulkCreateResponse)
async def bulk_create_students(
    org_id: UUID4,
    request: schemas.BulkCreateStudentsRequest,
    db: Session = Depends(get_db),
    admin_member: schemas.AuthenticatedMember = Depends(auth.require_admin_role)
):
    """Bulk create student profiles."""
    service = services.StudentGuardianService(db)
    results = service.bulk_create_students(org_id, request.students)
    return {
        "created": len(results),
        "profiles": [p[0] for p in results]
    }

@router.post("/guardians/bulk", response_model=schemas.BulkCreateResponse)
async def bulk_create_guardians(
    org_id: UUID4,
    request: schemas.BulkCreateGuardiansRequest,
    db: Session = Depends(get_db),
    admin_member: schemas.AuthenticatedMember = Depends(auth.require_admin_role)
):
    """Bulk create guardian profiles."""
    service = services.StudentGuardianService(db)
    results = service.bulk_create_guardians(org_id, request.guardians)
    return {
        "created": len(results),
        "profiles": [p[0] for p in results]
    }

@router.post("/pairs/bulk", response_model=schemas.BulkCreatePairsResponse)
async def bulk_create_and_link_pairs(
    org_id: UUID4,
    request: schemas.BulkCreatePairsRequest,
    db: Session = Depends(get_db),
    admin_member: schemas.AuthenticatedMember = Depends(auth.require_admin_role)
):
    """
    Bulk create student-guardian pairs and link them.
    Perfect for CSV uploads or external API integration.
    """
    service = services.StudentGuardianService(db)
    results = service.bulk_create_and_link(org_id, request.pairs)
    return {
        "created": len(results),
        "pairs": results
    }
