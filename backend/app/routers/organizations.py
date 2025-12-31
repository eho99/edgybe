from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload
from .. import models, schemas, auth
from ..db import get_db
from ..models.organization_member import OrganizationMember, OrgRole, MemberStatus
from pydantic import UUID4
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/organizations",
    tags=["Organizations"],
)

SENSITIVE_FIELDS = {
    "aeries_school_code",
    "sis_source_id",
    "sis_client_id",
    "sis_client_secret",
}

RESTRICTED_VIEW_ROLES = {OrgRole.staff, OrgRole.secretary}


def _sanitize_organization(
    organization: models.Organization, hide_sensitive: bool = False
) -> schemas.Organization:
    """
    Convert a SQLAlchemy Organization into a schema while optionally
    hiding sensitive integrations/foreign keys.
    """
    schema_data = schemas.Organization.model_validate(
        organization, from_attributes=True
    ).model_dump()

    # Extract district_name from the relationship
    if organization.district:
        schema_data["district_name"] = organization.district.name
    else:
        schema_data["district_name"] = None

    if hide_sensitive:
        for field in SENSITIVE_FIELDS:
            schema_data[field] = None

    return schemas.Organization(**schema_data)


def _reject_district_assignment(payload: object) -> None:
    """
    Prevent create/update callers from attempting to mutate the district link.
    """
    if isinstance(payload, dict) and "district_id" in payload:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="district_id is managed by the platform and cannot be modified via this endpoint.",
        )


def _ensure_user_is_admin(db: Session, user: schemas.SupabaseUser) -> None:
    """
    Ensure the current user has at least one active admin membership
    before allowing platform-level organization management (e.g. create).
    """
    admin_membership = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.user_id == user.id,
            OrganizationMember.role == OrgRole.admin,
            OrganizationMember.status == MemberStatus.active,
        )
        .first()
    )

    if not admin_membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin membership required to manage organizations.",
        )

@router.get("/my-memberships", response_model=List[schemas.OrganizationMembership])
async def get_my_organization_memberships(
    memberships: List[schemas.OrganizationMembership] = Depends(auth.get_user_organizations)
):
    """
    Get all organization memberships for the current user.
    Now uses the centralized auth dependency.
    """
    return memberships

@router.get("/{org_id}/protected-data", response_model=schemas.AuthenticatedMember)
async def get_organization_protected_data(
    org_id: UUID4,
    # This dependency blocks all unauthorized access
    member: schemas.AuthenticatedMember = Depends(auth.get_current_active_member)
):
    """
    An example protected endpoint. Only active members of `org_id`
    can access this.
    """
    # You now know the user is authenticated and is an active member
    # of this org. `member` contains their user_id, org_id, and role.
    
    return member

# ============================================================================
# EXAMPLES OF ROLE-BASED ENDPOINTS
# ============================================================================

@router.get("/{org_id}/admin-only-data")
async def get_admin_only_data(
    org_id: UUID4,
    admin_member: schemas.AuthenticatedMember = Depends(auth.require_admin_role)
):
    """
    Example endpoint that requires ADMIN role.
    Only organization admins can access this data.
    """
    return {
        "message": "This is admin-only data",
        "admin_user": admin_member.user.email,
        "organization_id": admin_member.org_id
    }

@router.get("/{org_id}/secretary-content")
async def get_secretary_content(
    org_id: UUID4,
    member: schemas.AuthenticatedMember = Depends(auth.require_admin_or_secretary_role)
):
    """
    Example endpoint that requires ADMIN or SECRETARY role.
    STAFF, GUARDIAN, and STUDENT roles are blocked from accessing this content.
    """
    return {
        "message": "This content is for admins and secretaries only",
        "user_role": member.role,
        "organization_id": member.org_id
    }

@router.get("/{org_id}/active-member-content")
async def get_active_member_content(
    org_id: UUID4,
    member: schemas.AuthenticatedMember = Depends(auth.require_active_role)
):
    """
    Example endpoint that requires active member role (admin, secretary, or staff).
    GUARDIAN and STUDENT roles are blocked from accessing this content.
    """
    return {
        "message": "This content is for active members only (admin, secretary, staff)",
        "user_role": member.role,
        "organization_id": member.org_id
    }

@router.get("/{org_id}/all-member-content")
async def get_all_member_content(
    org_id: UUID4,
    member: schemas.AuthenticatedMember = Depends(auth.require_any_role)
):
    """
    Example endpoint that allows any active member (including guardians and students).
    """
    return {
        "message": "This content is visible to all organization members",
        "user_role": member.role,
        "organization_id": member.org_id
    }

@router.get("/my-default-org")
async def get_my_default_organization(
    member: schemas.AuthenticatedMember = Depends(auth.get_user_default_organization)
):
    """
    Example endpoint that uses the user's default organization.
    Useful when you don't need org_id in the URL.
    """
    return {
        "message": "Using your default organization",
        "organization_id": member.org_id,
        "role": member.role,
        "user": member.user.email
    }


@router.post(
    "/",
    response_model=schemas.Organization,
    status_code=status.HTTP_201_CREATED,
)
async def create_organization(
    organization_in: schemas.OrganizationCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: schemas.SupabaseUser = Depends(auth.get_current_user),
):
    """
    Create a new organization. Only available to users with any admin membership.
    """
    _ensure_user_is_admin(db, user)

    payload = await request.json()
    _reject_district_assignment(payload)

    organization = models.Organization(**organization_in.model_dump())
    db.add(organization)
    db.commit()
    
    # Reload with district relationship
    organization = (
        db.query(models.Organization)
        .options(joinedload(models.Organization.district))
        .filter(models.Organization.id == organization.id)
        .first()
    )

    return _sanitize_organization(organization, hide_sensitive=False)


@router.get("/", response_model=List[schemas.Organization])
async def list_organizations(
    db: Session = Depends(get_db),
    user: schemas.SupabaseUser = Depends(auth.get_current_user),
):
    """
    List organizations that the current user is actively a member of.
    Staff and secretary roles receive a sanitized subset of fields.
    """
    memberships: List[Tuple[models.Organization, OrgRole]] = (
        db.query(models.Organization, OrganizationMember.role)
        .join(
            OrganizationMember,
            OrganizationMember.organization_id == models.Organization.id,
        )
        .options(joinedload(models.Organization.district))
        .filter(
            OrganizationMember.user_id == user.id,
            OrganizationMember.status == MemberStatus.active,
        )
        .all()
    )

    return [
        _sanitize_organization(
            organization,
            hide_sensitive=role in RESTRICTED_VIEW_ROLES,
        )
        for organization, role in memberships
    ]


@router.get("/{org_id}", response_model=schemas.Organization)
async def get_organization(
    org_id: UUID4,
    db: Session = Depends(get_db),
    member: schemas.AuthenticatedMember = Depends(auth.require_active_role),
):
    """
    Retrieve a single organization. Staff/secretary roles receive sanitized data.
    """
    organization = (
        db.query(models.Organization)
        .options(joinedload(models.Organization.district))
        .filter(models.Organization.id == org_id)
        .first()
    )

    if not organization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")

    hide_sensitive = member.role in RESTRICTED_VIEW_ROLES
    return _sanitize_organization(organization, hide_sensitive)


@router.patch("/{org_id}", response_model=schemas.Organization)
async def update_organization(
    org_id: UUID4,
    organization_update: schemas.OrganizationUpdate,
    request: Request,
    db: Session = Depends(get_db),
    member: schemas.AuthenticatedMember = Depends(auth.require_admin_role),
):
    """
    Update an existing organization. Admin role required, deletion not supported.
    """
    organization = (
        db.query(models.Organization)
        .options(joinedload(models.Organization.district))
        .filter(models.Organization.id == org_id)
        .first()
    )

    if not organization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")

    payload = await request.json()
    _reject_district_assignment(payload)

    update_data = organization_update.model_dump(exclude_unset=True)
    
    # Explicitly handle assignment_config from raw payload
    # This ensures it's processed even when None (to allow clearing the config)
    # Pydantic's exclude_unset=True might exclude None values that match defaults
    if "assignment_config" in payload:
        logger.info(f"Received assignment_config in payload: {payload['assignment_config']}")
        # Always include assignment_config if it's in the payload, even if None
        update_data["assignment_config"] = payload["assignment_config"]
        logger.info(f"Setting assignment_config in update_data: {update_data.get('assignment_config')}")

    logger.info(f"Update data keys: {list(update_data.keys())}")
    logger.info(f"assignment_config in update_data: {'assignment_config' in update_data}")

    # Apply updates
    for key, value in update_data.items():
        setattr(organization, key, value)
    
    # Verify assignment_config was set
    logger.info(f"Organization assignment_config after setattr: {organization.assignment_config}")
    
    db.add(organization)
    db.commit()
    db.refresh(organization)
    
    # Verify after commit
    logger.info(f"Organization assignment_config after commit: {organization.assignment_config}")
    
    # Reload with district relationship
    organization = (
        db.query(models.Organization)
        .options(joinedload(models.Organization.district))
        .filter(models.Organization.id == org_id)
        .first()
    )

    hide_sensitive = member.role in RESTRICTED_VIEW_ROLES
    return _sanitize_organization(organization, hide_sensitive)

