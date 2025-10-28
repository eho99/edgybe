import os
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from supabase import create_client, Client
from supabase_auth.errors import AuthApiError
from . import schemas
from .db import get_db
from .models.organization_member import OrganizationMember, MemberStatus, OrgRole
from sqlalchemy.orm import Session
from pydantic import UUID4
from typing import List, Optional

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")


# Create a single, reusable Supabase admin client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # We don't use tokenUrl, but it's needed

async def get_current_user(request: Request) -> schemas.SupabaseUser:
    """Dependency to get the user from Supabase JWT."""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    token = auth_header.replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=401, detail="Invalid token format")

    try:
        user_response = supabase.auth.get_user(token)
        user = user_response.user
        if not user:
             raise HTTPException(status_code=401, detail="Invalid token or user not found")
        
        return schemas.SupabaseUser(id=user.id, email=user.email)
    
    except AuthApiError as e:
        raise HTTPException(status_code=401, detail=f"Authentication error: {e.message}")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

async def get_current_active_member(
    request: Request,
    org_id: UUID4,
    db: Session = Depends(get_db),
    user: schemas.SupabaseUser = Depends(get_current_user)
) -> schemas.AuthenticatedMember:
    """
    Dependency that verifies the user is an *active member* of the
    organization specified in the path.
    """
    try:
        member = db.query(OrganizationMember).filter(
            OrganizationMember.user_id == user.id,
            OrganizationMember.organization_id == org_id
        ).first()

        if not member:
            raise HTTPException(status_code=403, detail="User not a member of this organization")
        
        if member.status != MemberStatus.active:
            raise HTTPException(status_code=403, detail="User is inactive in this organization")

        return schemas.AuthenticatedMember(
            user=user,
            org_id=member.organization_id,
            role=member.role
        )
    except Exception as e:
        raise HTTPException(status_code=403, detail=f"Access denied: {str(e)}")

# ============================================================================
# REUSABLE AUTH DEPENDENCIES FOR ORG AND ROLE-BASED ACCESS
# ============================================================================

async def get_user_organizations(
    db: Session = Depends(get_db),
    user: schemas.SupabaseUser = Depends(get_current_user)
) -> List[schemas.OrganizationMembership]:
    """
    Get all organization memberships for the current user.
    Useful when you need to know which orgs a user belongs to.
    """
    try:
        memberships = db.query(OrganizationMember).join(
            OrganizationMember.organization
        ).filter(
            OrganizationMember.user_id == user.id,
            OrganizationMember.status == MemberStatus.active
        ).all()
        
        result = []
        for membership in memberships:
            result.append(schemas.OrganizationMembership(
                org_id=membership.organization_id,
                role=membership.role,
                organization_name=membership.organization.name,
                joined_at=membership.joined_at
            ))
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch memberships: {str(e)}")

async def get_user_default_organization(
    db: Session = Depends(get_db),
    user: schemas.SupabaseUser = Depends(get_current_user)
) -> schemas.AuthenticatedMember:
    """
    Get the user's first/default organization membership.
    Useful when you don't need a specific org_id in the URL.
    """
    try:
        membership = db.query(OrganizationMember).join(
            OrganizationMember.organization
        ).filter(
            OrganizationMember.user_id == user.id,
            OrganizationMember.status == MemberStatus.active
        ).first()

        if not membership:
            raise HTTPException(status_code=403, detail="User is not a member of any organization")
        
        return schemas.AuthenticatedMember(
            user=user,
            org_id=membership.organization_id,
            role=membership.role
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch default organization: {str(e)}")

# ============================================================================
# ROLE-BASED PERMISSION DEPENDENCIES
# ============================================================================

async def require_admin_role(
    org_id: UUID4,
    db: Session = Depends(get_db),
    user: schemas.SupabaseUser = Depends(get_current_user)
) -> schemas.AuthenticatedMember:
    """
    Dependency that requires the user to be an ADMIN of the specified organization.
    """
    member = await get_current_active_member(Request(), org_id, db, user)
    if member.role != OrgRole.admin:
        raise HTTPException(status_code=403, detail="Admin role required")
    return member

async def require_admin_or_member_role(
    org_id: UUID4,
    db: Session = Depends(get_db),
    user: schemas.SupabaseUser = Depends(get_current_user)
) -> schemas.AuthenticatedMember:
    """
    Dependency that requires the user to be an ADMIN or MEMBER of the specified organization.
    Blocks VIEWER role.
    """
    member = await get_current_active_member(Request(), org_id, db, user)
    if member.role not in [OrgRole.admin, OrgRole.member]:
        raise HTTPException(status_code=403, detail="Admin or member role required")
    return member

async def require_any_role(
    org_id: UUID4,
    db: Session = Depends(get_db),
    user: schemas.SupabaseUser = Depends(get_current_user)
) -> schemas.AuthenticatedMember:
    """
    Dependency that requires the user to be any active member of the specified organization.
    This is equivalent to get_current_active_member but with a clearer name.
    """
    return await get_current_active_member(Request(), org_id, db, user)

# ============================================================================
# HELPER FUNCTIONS FOR ROLE CHECKING
# ============================================================================

def has_role_permission(user_role: OrgRole, required_roles: List[OrgRole]) -> bool:
    """
    Check if a user's role has permission based on required roles.
    
    Args:
        user_role: The user's current role
        required_roles: List of roles that have permission
    
    Returns:
        True if user has permission, False otherwise
    """
    return user_role in required_roles

def can_manage_users(user_role: OrgRole) -> bool:
    """Check if user can manage other users (admin only)."""
    return user_role == OrgRole.admin

def can_create_content(user_role: OrgRole) -> bool:
    """Check if user can create content (admin or member)."""
    return user_role in [OrgRole.admin, OrgRole.member]

def can_view_content(user_role: OrgRole) -> bool:
    """Check if user can view content (any role)."""
    return user_role in [OrgRole.admin, OrgRole.member, OrgRole.viewer]

def get_role_hierarchy_level(role: OrgRole) -> int:
    """
    Get the hierarchy level of a role (higher number = more permissions).
    Useful for comparing roles.
    """
    hierarchy = {
        OrgRole.viewer: 1,
        OrgRole.member: 2,
        OrgRole.admin: 3
    }
    return hierarchy.get(role, 0)

def role_has_permission(user_role: OrgRole, target_role: OrgRole) -> bool:
    """
    Check if user_role has permission to perform actions on target_role.
    Higher hierarchy roles can manage lower hierarchy roles.
    """
    return get_role_hierarchy_level(user_role) >= get_role_hierarchy_level(target_role)

