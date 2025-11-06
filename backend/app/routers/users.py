from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
import logging
from .. import models, schemas, auth
from ..db import get_db
from ..services.invitations import InvitationService, get_invitation_service

router = APIRouter(
    prefix="/api/v1/users/me",
    tags=["Current User"],
)

logger = logging.getLogger(__name__)

@router.get(
    "/profile",
    response_model=schemas.ProfileSchema
)
async def get_my_profile(
    # Protected by the base "get_current_user" dependency from auth.py
    db: Session = Depends(get_db),
    user: schemas.SupabaseUser = Depends(auth.get_current_user)
):
    """
    Gets the current authenticated user's profile.
    The frontend calls this on load to check 'has_completed_profile'.
    """
    logger.info(f"Attempting to fetch profile for user ID: {user.id}")
    logger.info(f"Type of user ID: {type(user.id)}")
    
    profile = db.query(models.Profile).filter(
        models.Profile.id == user.id
    ).first()
    
    if not profile:
        logger.error(f"Profile not found for user ID: {user.id}")
        # This should not happen if invitation service is working
        raise HTTPException(status_code=404, detail="Profile not found. Please contact support.")
    
    logger.info(f"Profile found for user ID: {user.id}. has_completed_profile: {profile.has_completed_profile}")
    return profile

@router.put(
    "/profile",
    response_model=schemas.ProfileSchema
)
async def update_my_profile(
    profile_data: schemas.ProfileUpdateSchema,
    db: Session = Depends(get_db),
    user: schemas.SupabaseUser = Depends(auth.get_current_user)
):
    """
    Updates the current user's profile and sets
    'has_completed_profile' to True. This is used for
    the one-time profile completion flow.
    """
    profile = db.query(models.Profile).filter(
        models.Profile.id == user.id
    ).first()
    
    if not profile:
        # Create a new profile if it doesn't exist (can happen with invited users)
        logger.info(f"Creating new profile for user {user.id} during profile completion")
        profile = models.Profile(
            id=user.id,
            full_name=profile_data.full_name,
            has_completed_profile=True
        )
        db.add(profile)
    else:
        # Update existing profile
        profile.full_name = profile_data.full_name
        profile.has_completed_profile = True # Mark as completed!
    
    db.commit()
    db.refresh(profile)
    
    # After creating/updating profile, try to link any pending organization memberships
    try:
        invitation_service = InvitationService(db)
        linked_member = invitation_service.link_invited_user_to_organization(
            user_id=user.id,
            email=user.email
        )
        
        if linked_member:
            logger.info(f"Successfully linked user {user.id} to organization {linked_member.organization_id}")
        else:
            logger.info(f"No organization memberships found to link for user {user.id}")
        
        # Mark invitations as accepted
        invitation_service.mark_invitation_accepted(user.email, user.id)
        
    except Exception as e:
        logger.error(f"Error linking organization memberships for user {user.id}: {str(e)}")
        # Don't fail the profile update if linking fails
        # The user can still complete their profile
    
    return profile

@router.post(
    "/link-invitation",
    response_model=schemas.OrganizationMemberPublic
)
async def link_invitation_to_user(
    db: Session = Depends(get_db),
    user: schemas.SupabaseUser = Depends(auth.get_current_user),
    invitation_service: InvitationService = Depends(get_invitation_service)
):
    """
    Links any pending organization memberships for the current user.
    This is called after a user accepts an invitation and creates their account.
    """
    linked_member = invitation_service.link_invited_user_to_organization(
        user_id=user.id,
        email=user.email
    )
    
    if not linked_member:
        raise HTTPException(status_code=404, detail="No pending invitations found for this user.")
    
    return linked_member

class PasswordResetRequest(BaseModel):
    email: EmailStr

@router.post(
    "/reset-password",
    response_model=dict
)
async def request_password_reset(
    request: PasswordResetRequest,
    db: Session = Depends(get_db),
    user: schemas.SupabaseUser = Depends(auth.get_current_user)
):
    """
    Request a password reset email for the current user.
    This is a self-service endpoint for users to reset their own password.
    """
    try:
        from ..auth import supabase
        
        # Verify the email matches the current user
        if user.email != request.email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only request password reset for your own account"
            )
        
        # Send password reset email
        supabase.auth.reset_password_for_email(
            request.email,
            {
                "redirect_to": "http://localhost:3000/reset-password"
            }
        )
        
        logger.info(f"Password reset email requested for {request.email}")
        return {"message": "Password reset email sent successfully"}
        
    except Exception as e:
        logger.error(f"Error generating password reset link for {request.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send password reset email: {str(e)}"
        )
