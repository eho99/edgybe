from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import Response
from pydantic import UUID4
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from typing import Optional, List
import logging
from datetime import datetime, timezone

from .. import schemas, auth, models
from ..db import get_db
from ..services import pdf_service, email_service, referral_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/organizations/{org_id}",
    tags=["Referrals"],
)


@router.get("/config/referrals", response_model=schemas.ReferralConfigResponse)
async def get_referral_config(
    org_id: UUID4,
    db: Session = Depends(get_db),
    member: schemas.AuthenticatedMember = Depends(auth.get_current_active_member)
):
    """
    Get referral configuration from organization preset_config.
    """
    import json
    
    org = db.query(models.Organization).filter(models.Organization.id == org_id).first()
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Check if preset_config exists and is not empty
    if not org.preset_config:
        logger.warning(f"Organization {org_id} has no preset_config. Cannot load referral config.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referral configuration not found for this organization"
        )
    
    # Parse config if it's a string
    config = org.preset_config
    if isinstance(config, str):
        try:
            config = json.loads(config)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse preset_config as JSON for org {org_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid configuration format"
            )
    
    # Handle cases where referral configuration is nested under "referral_config"
    if not isinstance(config, dict):
        logger.error(f"Organization {org_id} preset_config is not a dict: {type(config)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid referral configuration format: preset_config must be a dictionary"
        )
    
    if "referral_config" in config and isinstance(config["referral_config"], dict):
        referral_config = config["referral_config"]
    elif "referralConfig" in config and isinstance(config["referralConfig"], dict):
        referral_config = config["referralConfig"]
    else:
        referral_config = config

    if not referral_config or not isinstance(referral_config, dict):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid referral configuration format"
        )

    # Map keys to schema if needed
    # Schema expects: types, locations, time_of_day, behaviors, common_interventions
    # Actual config may have: referral_type, observed_behaviors (or types, behaviors)
    
    # Helper to extract options list if present, or use list directly
    # Supports fallback keys for different naming conventions
    def get_options(key, fallback_keys=None):
        # Try primary key first
        if key in referral_config:
            val = referral_config[key]
            if isinstance(val, dict) and 'options' in val:
                return val['options']
            if isinstance(val, list):
                return val
            return []
        
        # Try fallback keys if provided
        if fallback_keys:
            for fallback_key in fallback_keys:
                if fallback_key in referral_config:
                    val = referral_config[fallback_key]
                    if isinstance(val, dict) and 'options' in val:
                        return val['options']
                    if isinstance(val, list):
                        return val
                    return []
        
        logger.warning(f"Key '{key}' (and fallbacks {fallback_keys}) not found in referral_config. Available keys: {list(referral_config.keys())}")
        return []

    # Helper to get dict object (for location, time_of_day, behaviors)
    # Supports fallback keys for different naming conventions
    def get_dict(key, fallback_keys=None):
        result = {}
        # Try primary key first
        if key in referral_config and isinstance(referral_config[key], dict):
            result = referral_config[key].copy()
        # If key exists but is a list, wrap it in options
        elif key in referral_config and isinstance(referral_config[key], list):
            result = {"options": referral_config[key], "label": key}
        # Try fallback keys if provided
        elif fallback_keys:
            for fallback_key in fallback_keys:
                if fallback_key in referral_config and isinstance(referral_config[fallback_key], dict):
                    result = referral_config[fallback_key].copy()
                    break
                elif fallback_key in referral_config and isinstance(referral_config[fallback_key], list):
                    result = {"options": referral_config[fallback_key], "label": fallback_key}
                    break
        
        # Ensure allowOther is preserved (support both camelCase and snake_case)
        if not result:
            logger.warning(f"Key '{key}' (and fallbacks {fallback_keys}) not found in referral_config. Available keys: {list(referral_config.keys())}")
            result = {"options": [], "label": key}
        
        # Normalize allowOther field (support both camelCase and snake_case)
        if "allowOther" in result:
            result["allowOther"] = result["allowOther"]
        elif "allow_other" in result:
            result["allowOther"] = result.pop("allow_other")
        else:
            result["allowOther"] = False
        
        return result

    # Map actual config keys to expected schema keys
    # types can come from "types" or "referral_type"
    # behaviors can come from "behaviors" or "observed_behaviors"
    response_data = {
        "types": get_options("types", fallback_keys=["referral_type"]),
        "locations": get_dict("locations"),
        "time_of_day": get_dict("time_of_day"),
        "behaviors": get_dict("behaviors", fallback_keys=["observed_behaviors"]),
        "common_interventions": get_options("common_interventions")
    }
    
    # Log if we're returning empty configs (for debugging)
    if not response_data["types"] and not response_data["locations"].get("options") and not response_data["behaviors"].get("options"):
        logger.warning(f"Returning mostly empty referral config. referral_config keys: {list(referral_config.keys())}")
    
    return schemas.ReferralConfigResponse(**response_data)


@router.get("/referrals/stats", response_model=schemas.ReferralStatsResponse)
async def get_referral_stats_endpoint(
    org_id: UUID4,
    start_date: Optional[datetime] = Query(None, description="ISO8601 start date (inclusive)"),
    end_date: Optional[datetime] = Query(None, description="ISO8601 end date (inclusive)"),
    location: Optional[str] = Query(None, description="Filter by referral location"),
    time_of_day: Optional[str] = Query(None, description="Filter by time of day"),
    behaviors: Optional[List[str]] = Query(
        None, description="Filter by one or more observed behaviors"
    ),
    recent_limit: int = Query(
        5,
        ge=1,
        le=20,
        description="Number of recent referrals to return",
    ),
    db: Session = Depends(get_db),
    member: schemas.AuthenticatedMember = Depends(auth.get_current_active_member),
):
    """
    Retrieve referral statistics for a given organization within a time range.
    """
    try:
        stats = referral_service.get_referral_stats(
            db=db,
            org_id=org_id,
            start_date=start_date,
            end_date=end_date,
            location=location,
            time_of_day=time_of_day,
            behaviors=behaviors,
            recent_limit=recent_limit,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    return schemas.ReferralStatsResponse(**stats)


@router.get("/config/email-variables")
async def get_email_variables_endpoint(
    org_id: UUID4,
    member: schemas.AuthenticatedMember = Depends(auth.get_current_active_member)
):
    """
    Get available email variables.
    """
    return email_service.get_email_variables()


@router.post("/referrals", response_model=schemas.ReferralResponse)
async def create_referral(
    org_id: UUID4,
    referral_data: schemas.ReferralCreate,
    db: Session = Depends(get_db),
    member: schemas.AuthenticatedMember = Depends(auth.get_current_active_member)
):
    """
    Create a new referral. Staff and higher can create referrals.
    """
    # Validate student belongs to organization
    student_membership = db.query(models.OrganizationMember).filter(
        and_(
            models.OrganizationMember.organization_id == org_id,
            models.OrganizationMember.user_id == referral_data.student_id,
            models.OrganizationMember.role == models.OrgRole.student
        )
    ).first()
    
    if not student_membership:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student not found in this organization"
        )
    
    # Create referral
    referral = models.Referral(
        organization_id=org_id,
        student_id=referral_data.student_id,
        author_id=member.user.id,
        status="SUBMITTED",
        type=referral_data.type,
        location=referral_data.location,
        time_of_day=referral_data.time_of_day,
        behaviors=referral_data.behaviors,
        description=referral_data.description
    )
    
    db.add(referral)
    db.commit()
    db.refresh(referral)
    
    # Fetch related data
    student = db.query(models.Profile).filter(models.Profile.id == referral.student_id).first()
    author = db.query(models.Profile).filter(models.Profile.id == referral.author_id).first()
    
    return schemas.ReferralResponse(
        **referral.__dict__,
        student_name=student.full_name if student else None,
        student_student_id=student.student_id if student else None,
        student_grade_level=student.grade_level if student else None,
        author_name=author.full_name if author else None,
        interventions=[]
    )


@router.get("/referrals", response_model=schemas.ReferralListResponse)
async def list_referrals(
    org_id: UUID4,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    student_id: Optional[UUID4] = None,
    status: Optional[str] = None,
    type: Optional[str] = None,
    author_id: Optional[UUID4] = None,
    include_archived: bool = Query(False, description="Include archived referrals in results"),
    db: Session = Depends(get_db),
    member: schemas.AuthenticatedMember = Depends(auth.get_current_active_member)
):
    """
    List referrals with pagination and filters.
    Admin/Secretary see all, Staff see only their own.
    By default, archived referrals are excluded. Set include_archived=true to include them.
    """
    query = db.query(models.Referral).filter(
        models.Referral.organization_id == org_id
    )
    
    # Role-based filtering: staff only see their own referrals
    if member.role == models.OrgRole.staff:
        query = query.filter(models.Referral.author_id == member.user.id)
    
    # Filter out archived referrals by default
    # IMPORTANT: This requires the migration 'add_referral_archiving' (f8a9b0c1d2e3) to be run
    # Run: alembic upgrade head
    if not include_archived:
        query = query.filter(models.Referral.archived.is_(False))
    
    # Apply filters
    if student_id:
        query = query.filter(models.Referral.student_id == student_id)
    if status:
        query = query.filter(models.Referral.status == status)
    if type:
        query = query.filter(models.Referral.type == type)
    if author_id:
        query = query.filter(models.Referral.author_id == author_id)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * per_page
    referrals = query.order_by(models.Referral.created_at.desc()).offset(offset).limit(per_page).all()
    
    # Build response with nested data
    referral_items = []
    for referral in referrals:
        student = db.query(models.Profile).filter(models.Profile.id == referral.student_id).first()
        author = db.query(models.Profile).filter(models.Profile.id == referral.author_id).first()
        intervention_count = db.query(func.count(models.Intervention.id)).filter(
            models.Intervention.referral_id == referral.id
        ).scalar()
        
        referral_items.append(schemas.ReferralListItem(
            **referral.__dict__,
            student_name=student.full_name if student else None,
            student_student_id=student.student_id if student else None,
            author_name=author.full_name if author else None,
            intervention_count=intervention_count or 0
        ))
    
    total_pages = (total + per_page - 1) // per_page
    
    return schemas.ReferralListResponse(
        referrals=referral_items,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )


@router.get("/referrals/{referral_id}", response_model=schemas.ReferralResponse)
async def get_referral(
    org_id: UUID4,
    referral_id: UUID4,
    db: Session = Depends(get_db),
    member: schemas.AuthenticatedMember = Depends(auth.get_current_active_member)
):
    """
    Get a single referral with interventions.
    Admin/Secretary see all, Staff see only their own.
    """
    referral = db.query(models.Referral).filter(
        and_(
            models.Referral.id == referral_id,
            models.Referral.organization_id == org_id
        )
    ).first()
    
    if not referral:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referral not found"
        )
    
    # Check permissions: staff can only see their own referrals
    if member.role == models.OrgRole.staff and referral.author_id != member.user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this referral"
        )
    
    # Fetch related data
    student = db.query(models.Profile).filter(models.Profile.id == referral.student_id).first()
    author = db.query(models.Profile).filter(models.Profile.id == referral.author_id).first()
    
    # Fetch interventions
    interventions = db.query(models.Intervention).filter(
        models.Intervention.referral_id == referral_id
    ).order_by(models.Intervention.created_at.desc()).all()
    
    intervention_responses = []
    for intervention in interventions:
        creator = db.query(models.Profile).filter(models.Profile.id == intervention.created_by).first()
        intervention_responses.append(schemas.InterventionResponse(
            **intervention.__dict__,
            creator_name=creator.full_name if creator else None
        ))
    
    return schemas.ReferralResponse(
        **referral.__dict__,
        student_name=student.full_name if student else None,
        student_student_id=student.student_id if student else None,
        student_grade_level=student.grade_level if student else None,
        author_name=author.full_name if author else None,
        interventions=intervention_responses
    )


@router.patch("/referrals/{referral_id}", response_model=schemas.ReferralResponse)
async def update_referral(
    org_id: UUID4,
    referral_id: UUID4,
    update_data: schemas.ReferralUpdate,
    db: Session = Depends(get_db),
    member: schemas.AuthenticatedMember = Depends(auth.get_current_active_member)
):
    """
    Update a referral.
    Admin/Secretary can update any, Staff can update only their own.
    """
    referral = db.query(models.Referral).filter(
        and_(
            models.Referral.id == referral_id,
            models.Referral.organization_id == org_id
        )
    ).first()
    
    if not referral:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referral not found"
        )
    
    # Check permissions
    if member.role == models.OrgRole.staff and referral.author_id != member.user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this referral"
        )
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(referral, key, value)
    
    db.commit()
    db.refresh(referral)
    
    # Fetch related data
    student = db.query(models.Profile).filter(models.Profile.id == referral.student_id).first()
    author = db.query(models.Profile).filter(models.Profile.id == referral.author_id).first()
    
    # Fetch interventions
    interventions = db.query(models.Intervention).filter(
        models.Intervention.referral_id == referral_id
    ).all()
    
    intervention_responses = []
    for intervention in interventions:
        creator = db.query(models.Profile).filter(models.Profile.id == intervention.created_by).first()
        intervention_responses.append(schemas.InterventionResponse(
            **intervention.__dict__,
            creator_name=creator.full_name if creator else None
        ))
    
    return schemas.ReferralResponse(
        **referral.__dict__,
        student_name=student.full_name if student else None,
        student_student_id=student.student_id if student else None,
        student_grade_level=student.grade_level if student else None,
        author_name=author.full_name if author else None,
        interventions=intervention_responses
    )


@router.post("/referrals/{referral_id}/archive", response_model=schemas.ReferralResponse)
async def archive_referral(
    org_id: UUID4,
    referral_id: UUID4,
    db: Session = Depends(get_db),
    member: schemas.AuthenticatedMember = Depends(auth.get_current_active_member)
):
    """
    Archive a referral (soft delete).
    Admin/Secretary can archive any, Staff can archive only their own.
    """
    referral = db.query(models.Referral).filter(
        and_(
            models.Referral.id == referral_id,
            models.Referral.organization_id == org_id
        )
    ).first()
    
    if not referral:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referral not found"
        )
    
    # Check permissions
    if member.role == models.OrgRole.staff and referral.author_id != member.user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to archive this referral"
        )
    
    # Archive the referral
    referral.archived = True
    referral.archived_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(referral)
    
    # Fetch related data for response
    student = db.query(models.Profile).filter(models.Profile.id == referral.student_id).first()
    author = db.query(models.Profile).filter(models.Profile.id == referral.author_id).first()
    
    # Fetch interventions
    interventions = db.query(models.Intervention).filter(
        models.Intervention.referral_id == referral_id
    ).all()
    
    intervention_responses = []
    for intervention in interventions:
        creator = db.query(models.Profile).filter(models.Profile.id == intervention.created_by).first()
        intervention_responses.append(schemas.InterventionResponse(
            **intervention.__dict__,
            creator_name=creator.full_name if creator else None
        ))
    
    return schemas.ReferralResponse(
        **referral.__dict__,
        student_name=student.full_name if student else None,
        student_student_id=student.student_id if student else None,
        student_grade_level=student.grade_level if student else None,
        author_name=author.full_name if author else None,
        interventions=intervention_responses
    )


@router.post("/referrals/{referral_id}/unarchive", response_model=schemas.ReferralResponse)
async def unarchive_referral(
    org_id: UUID4,
    referral_id: UUID4,
    db: Session = Depends(get_db),
    member: schemas.AuthenticatedMember = Depends(auth.get_current_active_member)
):
    """
    Unarchive a referral (restore from archive).
    Admin/Secretary can unarchive any, Staff can unarchive only their own.
    """
    referral = db.query(models.Referral).filter(
        and_(
            models.Referral.id == referral_id,
            models.Referral.organization_id == org_id
        )
    ).first()
    
    if not referral:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referral not found"
        )
    
    # Check permissions
    if member.role == models.OrgRole.staff and referral.author_id != member.user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to unarchive this referral"
        )
    
    # Unarchive the referral
    referral.archived = False
    referral.archived_at = None
    
    db.commit()
    db.refresh(referral)
    
    # Fetch related data for response
    student = db.query(models.Profile).filter(models.Profile.id == referral.student_id).first()
    author = db.query(models.Profile).filter(models.Profile.id == referral.author_id).first()
    
    # Fetch interventions
    interventions = db.query(models.Intervention).filter(
        models.Intervention.referral_id == referral_id
    ).all()
    
    intervention_responses = []
    for intervention in interventions:
        creator = db.query(models.Profile).filter(models.Profile.id == intervention.created_by).first()
        intervention_responses.append(schemas.InterventionResponse(
            **intervention.__dict__,
            creator_name=creator.full_name if creator else None
        ))
    
    return schemas.ReferralResponse(
        **referral.__dict__,
        student_name=student.full_name if student else None,
        student_student_id=student.student_id if student else None,
        student_grade_level=student.grade_level if student else None,
        author_name=author.full_name if author else None,
        interventions=intervention_responses
    )


@router.post("/referrals/{referral_id}/interventions", response_model=schemas.InterventionResponse)
async def create_intervention(
    org_id: UUID4,
    referral_id: UUID4,
    intervention_data: schemas.InterventionCreate,
    db: Session = Depends(get_db),
    member: schemas.AuthenticatedMember = Depends(auth.get_current_active_member)
):
    """
    Create an intervention for a referral.
    """
    # Verify referral exists and belongs to org
    referral = db.query(models.Referral).filter(
        and_(
            models.Referral.id == referral_id,
            models.Referral.organization_id == org_id
        )
    ).first()
    
    if not referral:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referral not found"
        )
    
    # Check permissions
    if member.role == models.OrgRole.staff and referral.author_id != member.user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to add interventions to this referral"
        )
    
    # Create intervention
    intervention = models.Intervention(
        referral_id=referral_id,
        created_by=member.user.id,
        **intervention_data.model_dump()
    )
    
    db.add(intervention)
    db.commit()
    db.refresh(intervention)
    
    # Fetch creator
    creator = db.query(models.Profile).filter(models.Profile.id == intervention.created_by).first()
    
    return schemas.InterventionResponse(
        **intervention.__dict__,
        creator_name=creator.full_name if creator else None
    )


@router.get("/referrals/{referral_id}/interventions", response_model=List[schemas.InterventionResponse])
async def list_interventions(
    org_id: UUID4,
    referral_id: UUID4,
    db: Session = Depends(get_db),
    member: schemas.AuthenticatedMember = Depends(auth.get_current_active_member)
):
    """
    List all interventions for a referral.
    """
    # Verify referral exists and belongs to org
    referral = db.query(models.Referral).filter(
        and_(
            models.Referral.id == referral_id,
            models.Referral.organization_id == org_id
        )
    ).first()
    
    if not referral:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referral not found"
        )
    
    # Check permissions
    if member.role == models.OrgRole.staff and referral.author_id != member.user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view interventions for this referral"
        )
    
    interventions = db.query(models.Intervention).filter(
        models.Intervention.referral_id == referral_id
    ).order_by(models.Intervention.created_at.desc()).all()
    
    intervention_responses = []
    for intervention in interventions:
        creator = db.query(models.Profile).filter(models.Profile.id == intervention.created_by).first()
        intervention_responses.append(schemas.InterventionResponse(
            **intervention.__dict__,
            creator_name=creator.full_name if creator else None
        ))
    
    return intervention_responses


@router.patch("/referrals/{referral_id}/interventions/{intervention_id}", response_model=schemas.InterventionResponse)
async def update_intervention(
    org_id: UUID4,
    referral_id: UUID4,
    intervention_id: UUID4,
    update_data: schemas.InterventionUpdate,
    db: Session = Depends(get_db),
    member: schemas.AuthenticatedMember = Depends(auth.get_current_active_member)
):
    """
    Update an intervention.
    """
    # Verify referral exists and belongs to org
    referral = db.query(models.Referral).filter(
        and_(
            models.Referral.id == referral_id,
            models.Referral.organization_id == org_id
        )
    ).first()
    
    if not referral:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referral not found"
        )
    
    # Check permissions
    if member.role == models.OrgRole.staff and referral.author_id != member.user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update interventions for this referral"
        )
    
    # Get intervention
    intervention = db.query(models.Intervention).filter(
        and_(
            models.Intervention.id == intervention_id,
            models.Intervention.referral_id == referral_id
        )
    ).first()
    
    if not intervention:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intervention not found"
        )
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(intervention, key, value)
    
    db.commit()
    db.refresh(intervention)
    
    # Fetch creator
    creator = db.query(models.Profile).filter(models.Profile.id == intervention.created_by).first()
    
    return schemas.InterventionResponse(
        **intervention.__dict__,
        creator_name=creator.full_name if creator else None
    )


@router.get("/referrals/{referral_id}/pdf")
async def download_referral_pdf(
    org_id: UUID4,
    referral_id: UUID4,
    db: Session = Depends(get_db),
    member: schemas.AuthenticatedMember = Depends(auth.get_current_active_member)
):
    """
    Generate and download a PDF for a referral.
    """
    # Verify referral exists and belongs to org
    referral = db.query(models.Referral).filter(
        and_(
            models.Referral.id == referral_id,
            models.Referral.organization_id == org_id
        )
    ).first()
    
    if not referral:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referral not found"
        )
    
    # Check permissions
    if member.role == models.OrgRole.staff and referral.author_id != member.user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to download this referral"
        )
    
    # Fetch related data
    organization = db.query(models.Organization).filter(models.Organization.id == org_id).first()
    student = db.query(models.Profile).filter(models.Profile.id == referral.student_id).first()
    author = db.query(models.Profile).filter(models.Profile.id == referral.author_id).first()
    interventions = db.query(models.Intervention).filter(
        models.Intervention.referral_id == referral_id
    ).all()
    
    try:
        # Generate PDF
        pdf_bytes = pdf_service.generate_referral_pdf(
            referral=referral,
            organization=organization,
            student=student,
            author=author,
            interventions=interventions
        )
        
        # Return PDF as download
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=referral_{referral_id}.pdf"
            }
        )
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PDF generation service is not available"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF: {str(e)}"
        )


@router.post("/referrals/{referral_id}/email", response_model=schemas.EmailSendResponse)
async def send_referral_email_endpoint(
    org_id: UUID4,
    referral_id: UUID4,
    email_request: schemas.EmailRequest,
    db: Session = Depends(get_db),
    member: schemas.AuthenticatedMember = Depends(auth.get_current_active_member)
):
    """
    Send a referral via email with PDF attachment.
    """
    # Verify referral exists and belongs to org
    referral = db.query(models.Referral).filter(
        and_(
            models.Referral.id == referral_id,
            models.Referral.organization_id == org_id
        )
    ).first()
    
    if not referral:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referral not found"
        )
    
    # Check permissions
    if member.role == models.OrgRole.staff and referral.author_id != member.user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to email this referral"
        )
    
    # Fetch related data
    organization = db.query(models.Organization).filter(models.Organization.id == org_id).first()
    student = db.query(models.Profile).filter(models.Profile.id == referral.student_id).first()
    author = db.query(models.Profile).filter(models.Profile.id == referral.author_id).first()
    interventions = db.query(models.Intervention).filter(
        models.Intervention.referral_id == referral_id
    ).all()
    
    # Prepare email subject and message
    subject = email_request.subject or f"Student Referral Report for {student.full_name if student else 'Student'}"
    
    # If template_id provided, load and render template
    if email_request.template_id:
        template = db.query(models.EmailTemplate).filter(
            and_(
                models.EmailTemplate.id == email_request.template_id,
                models.EmailTemplate.is_active == True,
                or_(
                    models.EmailTemplate.organization_id == org_id,
                    models.EmailTemplate.scope == "system"
                )
            )
        ).first()
        
        if template:
            # Render template with referral context
            context = email_service.get_email_context_for_referral(referral, organization, student, author)
            subject = email_service.render_email_template(template.subject_template, context)
            message = email_service.render_email_template(template.body_template, context)
        else:
            message = email_request.message or f"Please find attached the referral report for {student.full_name if student else 'the student'}."
    else:
        message = email_request.message or f"Please find attached the referral report for {student.full_name if student else 'the student'}."
    
    try:
        # Generate PDF
        pdf_bytes = pdf_service.generate_referral_pdf(
            referral=referral,
            organization=organization,
            student=student,
            author=author,
            interventions=interventions
        )
        
        # Send email
        success, result_message, log_id = email_service.send_referral_email(
            db=db,
            referral_id=referral_id,
            recipient_emails=email_request.recipient_emails,
            subject=subject,
            message=message,
            pdf_bytes=pdf_bytes
        )
        
        if success:
            return schemas.EmailSendResponse(
                success=True,
                message=result_message,
                log_id=log_id
            )
        else:
            return schemas.EmailSendResponse(
                success=False,
                message=result_message,
                log_id=log_id
            )
            
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email or PDF service is not available"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}"
        )

# -------------------------------------------------------------------
# Email Template Endpoints
# -------------------------------------------------------------------

@router.post("/email-templates", response_model=schemas.EmailTemplateResponse)
async def create_email_template(
    org_id: UUID4,
    template_data: schemas.EmailTemplateCreate,
    db: Session = Depends(get_db),
    member: schemas.AuthenticatedMember = Depends(auth.require_admin_role)
):
    """
    Create a new email template. Only Admins.
    """
    template = models.EmailTemplate(
        organization_id=org_id,
        created_by_user_id=member.user.id,
        **template_data.model_dump()
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    # Fetch creator
    creator = db.query(models.Profile).filter(models.Profile.id == template.created_by_user_id).first()
    
    return schemas.EmailTemplateResponse(
        **template.__dict__,
        creator_name=creator.full_name if creator else None
    )


@router.get("/email-templates", response_model=schemas.EmailTemplateListResponse)
async def list_email_templates(
    org_id: UUID4,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    type: Optional[str] = None,
    db: Session = Depends(get_db),
    member: schemas.AuthenticatedMember = Depends(auth.get_current_active_member)
):
    """
    List email templates.
    Admins see all + system templates.
    Staff see active organization templates + system templates.
    """
    query = db.query(models.EmailTemplate).filter(
        or_(
            models.EmailTemplate.organization_id == org_id,
            models.EmailTemplate.scope == "system"
        )
    )
    
    # Staff only see active templates
    if member.role == models.OrgRole.staff:
        query = query.filter(models.EmailTemplate.is_active == True)
        
    if type:
        query = query.filter(models.EmailTemplate.type == type)
        
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * per_page
    templates = query.order_by(models.EmailTemplate.created_at.desc()).offset(offset).limit(per_page).all()
    
    template_responses = []
    for template in templates:
        creator = db.query(models.Profile).filter(models.Profile.id == template.created_by_user_id).first()
        template_responses.append(schemas.EmailTemplateResponse(
            **template.__dict__,
            creator_name=creator.full_name if creator else None
        ))
    
    total_pages = (total + per_page - 1) // per_page
    
    return schemas.EmailTemplateListResponse(
        templates=template_responses,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )


@router.get("/email-templates/{template_id}", response_model=schemas.EmailTemplateResponse)
async def get_email_template(
    org_id: UUID4,
    template_id: UUID4,
    db: Session = Depends(get_db),
    member: schemas.AuthenticatedMember = Depends(auth.get_current_active_member)
):
    """
    Get a single email template.
    """
    template = db.query(models.EmailTemplate).filter(
        and_(
            models.EmailTemplate.id == template_id,
            or_(
                models.EmailTemplate.organization_id == org_id,
                models.EmailTemplate.scope == "system"
            )
        )
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
        
    creator = db.query(models.Profile).filter(models.Profile.id == template.created_by_user_id).first()
    
    return schemas.EmailTemplateResponse(
        **template.__dict__,
        creator_name=creator.full_name if creator else None
    )


@router.patch("/email-templates/{template_id}", response_model=schemas.EmailTemplateResponse)
async def update_email_template(
    org_id: UUID4,
    template_id: UUID4,
    template_data: schemas.EmailTemplateUpdate,
    db: Session = Depends(get_db),
    member: schemas.AuthenticatedMember = Depends(auth.require_admin_role)
):
    """
    Update an email template. Only Admins.
    Cannot update system templates.
    """
    template = db.query(models.EmailTemplate).filter(
        and_(
            models.EmailTemplate.id == template_id,
            models.EmailTemplate.organization_id == org_id
        )
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found or you do not have permission to edit it"
        )
        
    # Update fields
    update_dict = template_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(template, key, value)
        
    db.commit()
    db.refresh(template)
    
    creator = db.query(models.Profile).filter(models.Profile.id == template.created_by_user_id).first()
    
    return schemas.EmailTemplateResponse(
        **template.__dict__,
        creator_name=creator.full_name if creator else None
    )


@router.delete("/email-templates/{template_id}")
async def delete_email_template(
    org_id: UUID4,
    template_id: UUID4,
    db: Session = Depends(get_db),
    member: schemas.AuthenticatedMember = Depends(auth.require_admin_role)
):
    """
    Delete an email template. Only Admins.
    Cannot delete system templates.
    """
    template = db.query(models.EmailTemplate).filter(
        and_(
            models.EmailTemplate.id == template_id,
            models.EmailTemplate.organization_id == org_id
        )
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found or you do not have permission to delete it"
        )
        
    db.delete(template)
    db.commit()
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)
