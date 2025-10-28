from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import UUID4

from .. import models, schemas, auth
from sqlalchemy.orm import Session
from ..db import get_db
from ..services.invitations import InvitationService, get_invitation_service

router = APIRouter(
    prefix="/api/v1/organizations/{org_id}/members",
    tags=["Organization Members"],
)

@router.post(
    "/invite",
    response_model=schemas.OrganizationMemberPublic,
)
async def invite_new_member(
    org_id: UUID4,
    invite_request: schemas.UserInviteRequest,
    # This is protected by the *existing* dependency from auth.py
    admin_member: schemas.AuthenticatedMember = Depends(auth.require_admin_role),
    invitation_service: InvitationService = Depends(get_invitation_service)
):
    """
    Directly invites a new user to the organization
    or adds an existing user to it.
    Only Admins can perform this action.
    """
    try:
        member = await invitation_service.invite_or_add_user_to_org(
            org_id=org_id,
            email=invite_request.email,
            role=invite_request.role,
            full_name=invite_request.full_name
        )
        return member
    except Exception as e:
        # Catch errors from the service
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to invite user: {str(e)}"
        )
