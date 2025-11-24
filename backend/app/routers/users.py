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

# Public router for unauthenticated endpoints
public_router = APIRouter(
    prefix="/api/v1/users",
    tags=["Users"],
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
            email=user.email,  # Sync email from Supabase Auth
            has_completed_profile=True
        )
        # Set new fields if provided
        if profile_data.email is not None:
            profile.email = profile_data.email
        if profile_data.phone is not None:
            profile.phone = profile_data.phone
        if profile_data.street_number is not None:
            profile.street_number = profile_data.street_number
        if profile_data.street_name is not None:
            profile.street_name = profile_data.street_name
        if profile_data.city is not None:
            profile.city = profile_data.city
        if profile_data.state is not None:
            profile.state = profile_data.state
        if profile_data.zip_code is not None:
            profile.zip_code = profile_data.zip_code
        if profile_data.country is not None:
            profile.country = profile_data.country
        if profile_data.preferred_language is not None:
            profile.preferred_language = profile_data.preferred_language
        if profile_data.grade_level is not None:
            profile.grade_level = profile_data.grade_level
        if profile_data.student_id is not None:
            profile.student_id = profile_data.student_id
        if profile_data.is_active is not None:
            profile.is_active = profile_data.is_active
        db.add(profile)
    else:
        # Update existing profile - update only provided fields
        # Sync email from Supabase Auth if not set or if user email changed
        if not profile.email or profile.email != user.email:
            profile.email = user.email
        # Allow manual email update if provided in request
        if profile_data.email is not None:
            profile.email = profile_data.email
        if profile_data.full_name is not None:
            profile.full_name = profile_data.full_name
        if profile_data.phone is not None:
            profile.phone = profile_data.phone
        if profile_data.street_number is not None:
            profile.street_number = profile_data.street_number
        if profile_data.street_name is not None:
            profile.street_name = profile_data.street_name
        if profile_data.city is not None:
            profile.city = profile_data.city
        if profile_data.state is not None:
            profile.state = profile_data.state
        if profile_data.zip_code is not None:
            profile.zip_code = profile_data.zip_code
        if profile_data.country is not None:
            profile.country = profile_data.country
        if profile_data.preferred_language is not None:
            profile.preferred_language = profile_data.preferred_language
        if profile_data.grade_level is not None:
            profile.grade_level = profile_data.grade_level
        if profile_data.student_id is not None:
            profile.student_id = profile_data.student_id
        if profile_data.is_active is not None:
            profile.is_active = profile_data.is_active
        # Mark as completed if full_name is being set (for profile completion flow)
        # Only set to True if full_name is provided, don't set to False if it's None
        if profile_data.full_name is not None and profile_data.full_name.strip():
            profile.has_completed_profile = True
    
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

@public_router.post(
    "/request-password-reset",
    response_model=dict
)
async def public_request_password_reset(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Public endpoint to request a password reset email.
    This is used from the login page when users forget their password.
    Does not require authentication.
    """
    try:
        from ..auth import supabase
        
        # Send password reset email
        supabase.auth.reset_password_for_email(
            request.email,
            {
                "redirect_to": "http://localhost:3000/reset-password"
            }
        )
        
        logger.info(f"Public password reset email requested for {request.email}")
        # Don't reveal if email exists or not for security
        return {"message": "If an account with that email exists, a password reset link has been sent."}
        
    except Exception as e:
        logger.error(f"Error sending password reset email for {request.email}: {str(e)}")
        # Don't reveal if email exists or not for security
        return {"message": "If an account with that email exists, a password reset link has been sent."}
