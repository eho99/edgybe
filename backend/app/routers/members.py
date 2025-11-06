from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import UUID4
from sqlalchemy import and_, or_
from typing import Optional
import logging

from .. import models, schemas, auth
from sqlalchemy.orm import Session
from ..db import get_db
from ..services.invitations import InvitationService, get_invitation_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/organizations/{org_id}/members",
    tags=["Organization Members"],
)

@router.post(
    "/invite",
    response_model=schemas.OrganizationMemberPublic
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
            full_name=invite_request.full_name,
            inviter_id=admin_member.user.id
        )
        return member
    except Exception as e:
        # Catch errors from the service
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to invite user: {str(e)}"
        )

@router.get(
    "/",
    response_model=schemas.AccountListResponse
)
async def list_accounts(
    org_id: UUID4,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    status_filter: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    admin_member: schemas.AuthenticatedMember = Depends(auth.require_admin_role)
):
    """
    List all organization members (accounts) with pagination and filtering.
    Includes both active and inactive members.
    Only Admins can perform this action.
    """
    try:
        # Build query - join with Profile to get user info
        query = db.query(models.OrganizationMember).join(
            models.Profile,
            models.OrganizationMember.user_id == models.Profile.id,
            isouter=True  # Left join to include members without profiles
        ).filter(
            models.OrganizationMember.organization_id == org_id
        )
        
        # Apply status filter
        if status_filter:
            try:
                status_enum = models.MemberStatus(status_filter)
                query = query.filter(models.OrganizationMember.status == status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status filter: {status_filter}. Must be 'active' or 'inactive'"
                )
        
        # Apply search filter (on email or full_name)
        if search:
            query = query.filter(
                or_(
                    models.Profile.full_name.ilike(f"%{search}%"),
                    models.OrganizationMember.invite_email.ilike(f"%{search}%")
                )
            )
        
        # Get total count before pagination
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        members = query.offset(offset).limit(per_page).all()
        
        # Fetch emails from Supabase Auth for all user_ids
        user_emails = {}
        user_ids = [m.user_id for m in members if m.user_id]
        
        if user_ids:
            try:
                from ..auth import supabase
                # Get all users from Supabase Auth
                users_response = supabase.auth.admin.list_users()
                if users_response and hasattr(users_response, 'data') and users_response.data:
                    for user in users_response.data:
                        if user.id in user_ids:
                            user_emails[user.id] = user.email
            except Exception as e:
                # Log error but continue - we'll show None for email if we can't fetch it
                logger.warning(f"Failed to fetch user emails from Supabase: {str(e)}")
        
        # Convert to response format
        account_responses = []
        for member in members:
            email = None
            if member.user_id and member.user_id in user_emails:
                email = user_emails[member.user_id]
            elif member.invite_email:
                email = member.invite_email
            
            full_name = None
            if member.user_profile:
                full_name = member.user_profile.full_name
            
            account_responses.append(schemas.AccountResponse(
                id=member.id,
                organization_id=member.organization_id,
                user_id=member.user_id,
                invite_email=member.invite_email,
                email=email,
                full_name=full_name,
                role=member.role,
                status=member.status,
                joined_at=member.joined_at
            ))
        
        total_pages = (total + per_page - 1) // per_page
        
        return schemas.AccountListResponse(
            accounts=account_responses,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list accounts: {str(e)}"
        )

@router.delete(
    "/{member_id}"
)
async def delete_account(
    org_id: UUID4,
    member_id: UUID4,
    db: Session = Depends(get_db),
    admin_member: schemas.AuthenticatedMember = Depends(auth.require_admin_role)
):
    """
    Delete an organization member account.
    Hard delete: Removes the member record from the database.
    Only Admins can perform this action.
    Cannot delete yourself.
    """
    try:
        # Find the member
        member = db.query(models.OrganizationMember).filter(
            and_(
                models.OrganizationMember.id == member_id,
                models.OrganizationMember.organization_id == org_id
            )
        ).first()
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        
        # Prevent admin from deleting themselves
        if member.user_id == admin_member.user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        # Hard delete: Remove the member record
        db.delete(member)
        db.commit()
        
        return {"message": "Account deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}"
        )
