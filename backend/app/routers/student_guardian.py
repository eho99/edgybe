from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import UUID4
from sqlalchemy.orm import Session
from sqlalchemy import or_
import logging

from .. import schemas, auth, services, models
from ..db import get_db
from ..schemas.user import ProfileUpdateSchema

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/organizations/{org_id}",
    tags=["Student-Guardian Relationships"],
)

def _list_profiles(
    *,
    db: Session,
    org_id: UUID4,
    role: models.OrgRole,
    page: int,
    per_page: int,
    search: str | None = None,
):
    query = db.query(models.Profile).join(
        models.OrganizationMember,
        models.OrganizationMember.user_id == models.Profile.id,
    ).filter(
        models.OrganizationMember.organization_id == org_id,
        models.OrganizationMember.role == role,
    )

    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                models.Profile.full_name.ilike(like),
                models.Profile.student_id.ilike(like),
                models.Profile.phone.ilike(like),
                models.Profile.city.ilike(like),
            )
        )

    total = query.count()
    offset = (page - 1) * per_page
    profiles = query.order_by(models.Profile.full_name.asc()).offset(offset).limit(per_page).all()
    total_pages = (total + per_page - 1) // per_page

    profile_schemas = [
        schemas.ProfileSchema.model_validate(profile)
        for profile in profiles
    ]

    return schemas.ProfileListResponse(
        profiles=profile_schemas,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )

@router.get("/students", response_model=schemas.ProfileListResponse)
async def list_students(
    org_id: UUID4,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    search: str | None = Query(None),
    db: Session = Depends(get_db),
    member: schemas.AuthenticatedMember = Depends(auth.require_active_role),
):
    """
    List students in the organization with optional search.
    Admin, Secretary, and Staff can access this endpoint.
    Search supports filtering by name, student_id, phone, or city.
    """
    return _list_profiles(
        db=db,
        org_id=org_id,
        role=models.OrgRole.student,
        page=page,
        per_page=per_page,
        search=search,
    )

@router.get("/guardians", response_model=schemas.ProfileListResponse)
async def list_guardians(
    org_id: UUID4,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    search: str | None = Query(None),
    db: Session = Depends(get_db),
    admin_member: schemas.AuthenticatedMember = Depends(auth.require_admin_role),
):
    return _list_profiles(
        db=db,
        org_id=org_id,
        role=models.OrgRole.guardian,
        page=page,
        per_page=per_page,
        search=search,
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
    
    # Fetch emails from Supabase Auth for guardians who have user accounts
    guardian_user_ids = [link.guardian_id for link in links if link.guardian_id]
    user_emails = {}
    
    if guardian_user_ids:
        try:
            from ..auth import supabase
            # Get all users from Supabase Auth
            users_response = supabase.auth.admin.list_users()
            # Handle different response formats: list directly or response object with .users/.data
            users_list = None
            if users_response:
                if isinstance(users_response, list):
                    # Direct list of User objects
                    users_list = users_response
                elif hasattr(users_response, 'users') and users_response.users:
                    # Response object with .users attribute
                    users_list = users_response.users
                elif hasattr(users_response, 'data') and users_response.data:
                    # Response object with .data attribute
                    users_list = users_response.data
            
            if users_list:
                for user in users_list:
                    # Convert user.id to UUID if it's a string (Supabase returns strings)
                    user_id = user.id
                    if isinstance(user_id, str):
                        from uuid import UUID
                        try:
                            user_id = UUID(user_id)
                        except (ValueError, AttributeError):
                            continue
                    
                    if user_id in guardian_user_ids:
                        user_emails[user_id] = user.email
        except Exception as e:
            # Log error but continue - we'll fall back to invite_email
            logger.warning(f"Failed to fetch guardian emails from Supabase: {str(e)}")
    
    enhanced_links = []
    for link in links:
        # Convert to Pydantic model first to handle nested relations
        link_data = schemas.GuardianLinkResponse.model_validate(link)
        
        # Get email from guardian's membership for this org using the relationship
        # This is more reliable than a separate query since we're using the same guardian object
        guardian_membership = next(
            (m for m in link.guardian.memberships if m.organization_id == org_id),
            None
        )
        
        # Try to get email from Supabase Auth first (for users with accounts),
        # then fall back to invite_email (for guardians created without accounts)
        guardian_email = None
        if link.guardian_id and link.guardian_id in user_emails:
            guardian_email = user_emails[link.guardian_id]
        elif guardian_membership and guardian_membership.invite_email:
            guardian_email = guardian_membership.invite_email
        
        link_data = link_data.model_copy(update={"guardian_email": guardian_email})
        enhanced_links.append(link_data)
    
    return {
        "student": student_profile,
        "guardians": enhanced_links
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

@router.patch("/students/{student_id}", response_model=schemas.ProfileSchema)
async def update_student_profile(
    org_id: UUID4,
    student_id: UUID4,
    profile_update: ProfileUpdateSchema,
    db: Session = Depends(get_db),
    admin_member: schemas.AuthenticatedMember = Depends(auth.require_admin_role),
):
    membership = db.query(models.OrganizationMember).filter(
        models.OrganizationMember.organization_id == org_id,
        models.OrganizationMember.user_id == student_id,
        models.OrganizationMember.role == models.OrgRole.student,
    ).first()

    if not membership:
        raise HTTPException(status_code=404, detail="Student not found in this organization")

    profile = db.query(models.Profile).filter(models.Profile.id == student_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")

    update_data = profile_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile

@router.patch("/guardians/{guardian_id}", response_model=schemas.ProfileSchema)
async def update_guardian_profile(
    org_id: UUID4,
    guardian_id: UUID4,
    profile_update: ProfileUpdateSchema,
    db: Session = Depends(get_db),
    admin_member: schemas.AuthenticatedMember = Depends(auth.require_admin_role),
):
    membership = db.query(models.OrganizationMember).filter(
        models.OrganizationMember.organization_id == org_id,
        models.OrganizationMember.user_id == guardian_id,
        models.OrganizationMember.role == models.OrgRole.guardian,
    ).first()

    if not membership:
        raise HTTPException(status_code=404, detail="Guardian not found in this organization")

    profile = db.query(models.Profile).filter(models.Profile.id == guardian_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Guardian profile not found")

    update_data = profile_update.model_dump(exclude_unset=True)
    # Guardians shouldn't receive student-specific fields
    update_data.pop("grade_level", None)
    update_data.pop("student_id", None)

    for field, value in update_data.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
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
