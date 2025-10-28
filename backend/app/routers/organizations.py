from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, auth
from ..db import get_db
from pydantic import UUID4

router = APIRouter(
    prefix="/api/v1/organizations",
    tags=["Organizations"],
)

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

# Add more endpoints here for:
# - Superadmin creating an org
# - Org admin inviting a user (uses supabase.auth.admin.invite_user_by_email)
# - Org admin updating a user's role or status

