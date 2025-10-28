from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, auth
from ..db import get_db
from pydantic import UUID4
from typing import List

router = APIRouter(
    prefix="/api/v1/organizations",
    tags=["Organizations"],
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

