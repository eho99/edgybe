from sqlalchemy.orm import Session
from pydantic import EmailStr, UUID4
from fastapi import Depends
from supabase_auth.errors import AuthApiError
import logging
from datetime import datetime, timedelta, timezone

from .. import models, schemas
from ..db import get_db
# Import the admin client from existing auth file
from ..auth import supabase  

logger = logging.getLogger(__name__)

class InvitationService:
    def __init__(self, db: Session):
        self.db = db

    async def invite_or_add_user_to_org(
        self,
        org_id: UUID4,
        email: EmailStr,
        role: models.OrgRole,
        full_name: str | None = None,
        inviter_id: UUID4 | None = None
    ) -> models.OrganizationMember:
        """
        Main service function.
        1. Checks if user exists in Supabase Auth.
        2. If not, invites them and creates a local profile.
        3. If so, fetches their local profile.
        4. Checks if they are already in the org.
        5. If not, adds them. If so, updates their role.
        """
        
        profile = None
        user_id = None

        try:
            logger.info(f"Checking if user {email} exists in Supabase Auth")
            users_response = supabase.auth.admin.list_users() # TODO: this is inefficient to index in O(n)
            existing_user = None

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
                    if user.email == email:
                        existing_user = user
                        break
            
            if existing_user:
                user_id = existing_user.id
                logger.info(f"User {email} found in Auth with ID: {user_id}")
                
                profile = self.db.query(models.Profile).filter(
                    models.Profile.id == user_id
                ).first()
                
                if not profile:
                    # User is in auth but not our DB? (Edge case - likely reactivation scenario)
                    # Since they're an existing user in Auth, mark profile as completed
                    logger.warning(f"User {email} exists in Auth but not in Profile DB. Creating profile with completed status.")
                    profile = self._create_local_profile(
                        user_id=user_id,
                        full_name=full_name or existing_user.email,
                        has_completed_profile=True  # Existing users should be marked as completed
                    )
                else:
                    # Profile exists - ensure it's marked as completed for reactivated users
                    # This handles cases where profile was created with incomplete status
                    if not profile.has_completed_profile:
                        logger.info(f"User {email} has existing profile with incomplete status. Marking as completed for reactivation.")
                        profile.has_completed_profile = True
                        if full_name and not profile.full_name:
                            profile.full_name = full_name
            else:
                # User does NOT exist in Auth. Invite them.
                logger.info(f"User {email} not found in Auth. Inviting...")
                invite_response = supabase.auth.admin.invite_user_by_email(
                    email,
                    options={
                        "redirect_to": "http://localhost:3000/invite-profile-completion"
                    }
                )
                
                logger.info(f"Invite response type: {type(invite_response)}")
                logger.info(f"Invite response: {invite_response}")
                
                # Create invitation record for tracking
                invitation = models.Invitation(
                    organization_id=org_id,
                    email=email,
                    role=role,
                    inviter_id=inviter_id,  # Use the actual inviter's user ID
                    status=models.InvitationStatus.pending
                )
                self.db.add(invitation)
                
                # Do NOT create a temporary profile. Create a pending membership tied to invite_email.
                member = models.OrganizationMember(
                    organization_id=org_id,
                    user_id=None,               # unknown until the user signs up
                    invite_email=email,         # used to link after acceptance
                    role=role,
                    status=models.MemberStatus.active
                )
                self.db.add(member)
                self.db.commit()
                self.db.refresh(member)
                self.db.refresh(invitation)
                
                logger.info(f"Invitation sent to {email}. Created invitation record and pending organization membership. Will link on acceptance.")
                return member
            
        except Exception as e:
            logger.error(f"Error in invitation process: {str(e)}")
            raise Exception(f"Failed to process invitation for {email}: {str(e)}")

        # Ensure user_id is set before checking membership
        if not user_id:
            raise Exception(f"User ID not set for email {email}. Cannot proceed with membership check.")

        # 4. Check if they are already in the organization (regardless of status)
        member = self.db.query(models.OrganizationMember).filter(
            models.OrganizationMember.user_id == user_id,
            models.OrganizationMember.organization_id == org_id
        ).first()

        if member:
            # 5. User is already in org (could be active or inactive)
            if member.status == models.MemberStatus.inactive:
                # Reactivate the account and update role
                logger.info(f"User {email} has inactive membership in org {org_id}. Reactivating and updating role to {role}.")
                member.status = models.MemberStatus.active
                member.role = role
                
                # Send password reset email for reactivated users
                try:
                    logger.info(f"Sending password reset email to reactivated user {email}")
                    supabase.auth.reset_password_for_email(
                        email,
                        {
                            "redirect_to": "http://localhost:3000/reset-password"
                        }
                    )
                    logger.info(f"Password reset email requested for {email}")
                except Exception as e:
                    logger.warning(f"Failed to send password reset email to {email}: {str(e)}")
                    # Don't fail reactivation if email fails
            else:
                # Active membership - just update role
                logger.info(f"User {email} already active in org {org_id}. Updating role to {role}.")
                member.role = role
        else:
            # 5. User is not in org. Add them.
            logger.info(f"Adding new user {email} to org {org_id} with role {role}.")
            member = models.OrganizationMember(
                organization_id=org_id,
                user_id=user_id,
                role=role,
                status=models.MemberStatus.active
            )
            self.db.add(member)

        # Commit all changes (new profile, new member, or role update)
        self.db.commit()
        self.db.refresh(member)
        # Refresh profile if it was updated
        if profile:
            self.db.refresh(profile)
        return member

    def _create_local_profile(
        self, user_id: UUID4, full_name: str | None, has_completed_profile: bool = False
    ) -> models.Profile:
        """Internal helper to create the profile row."""
        profile = models.Profile(
            id=user_id,
            full_name=full_name,
            has_completed_profile=has_completed_profile
        )
        self.db.add(profile)
        # We don't commit here; the calling function will commit.
        return profile

    def link_invited_user_to_organization(
        self, 
        user_id: UUID4, 
        email: str
    ) -> models.OrganizationMember | None:
        """
        When a user accepts an invitation and creates their account,
        this method links their real user_id to any temporary organization memberships
        that were created during the invitation process.
        """
        logger.info(f"Attempting to link user {user_id} (email: {email}) to organization memberships")
        
        # Strategy A: Link by pending membership invite_email first (preferred)
        pending_memberships = self.db.query(models.OrganizationMember).filter(
            models.OrganizationMember.invite_email == email,
            # user_id may be NULL for pending invites; we will set it here
            # no additional filter to ensure we update all pending invites for this email
        ).all()
        
        linked_members = []

        logger.info(f"Found {len(pending_memberships)} pending memberships by invite_email for {email}")
        for membership in pending_memberships:
            membership.user_id = user_id
            membership.invite_email = None
            linked_members.append(membership)
        
        # Strategy B: Remove legacy temp-profile fallback (we no longer create temp profiles)
        
        if linked_members:
            self.db.commit()
            logger.info(f"Successfully linked {len(linked_members)} organization memberships for user {user_id}")
            return linked_members[0]  # Return the first one
        
        logger.info(f"No organization memberships found to link for user {user_id}")
        return None

    def mark_invitation_accepted(self, email: str, user_id: UUID4) -> bool:
        """
        Mark invitation as accepted when user completes profile.
        """
        try:
            # Find pending invitations for this email
            invitations = self.db.query(models.Invitation).filter(
                models.Invitation.email == email,
                models.Invitation.status == models.InvitationStatus.pending
            ).all()
            
            if not invitations:
                logger.info(f"No pending invitations found for email {email}")
                return False
            
            # Mark all pending invitations as accepted
            for invitation in invitations:
                invitation.status = models.InvitationStatus.accepted
                invitation.accepted_at = datetime.now(timezone.utc)
            
            self.db.commit()
            logger.info(f"Marked {len(invitations)} invitations as accepted for email {email}")
            return True
            
        except Exception as e:
            logger.error(f"Error marking invitation as accepted for {email}: {str(e)}")
            return False

    async def resend_invitation(
        self,
        invitation_id: UUID4,
        org_id: UUID4
    ) -> tuple[bool, str]:
        """
        Resend an invitation email via Supabase.
        
        Args:
            invitation_id: The ID of the invitation to resend
            org_id: The organization ID (for verification)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Find the invitation
            invitation = self.db.query(models.Invitation).filter(
                models.Invitation.id == invitation_id,
                models.Invitation.organization_id == org_id
            ).first()
            
            if not invitation:
                logger.warning(f"Invitation {invitation_id} not found for org {org_id}")
                return (False, "Invitation not found")
            
            # Verify invitation is pending
            if invitation.status != models.InvitationStatus.pending:
                logger.warning(f"Attempted to resend non-pending invitation {invitation_id} with status {invitation.status}")
                return (False, f"Cannot resend invitation with status: {invitation.status}")
            
            # Check if invitation is expired
            now = datetime.now(timezone.utc)
            # Ensure expires_at is timezone-aware (assume UTC if naive)
            expires_at = invitation.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            is_expired = expires_at < now
            
            # Resend the invitation via Supabase
            try:
                logger.info(f"Resending invitation to {invitation.email} via Supabase")
                
                # Use the same redirect_to URL as original invitation
                redirect_to = "http://localhost:3000/invite-profile-completion"
                # TODO: Make this configurable via environment variable
                # redirect_to = os.getenv("NEXT_PUBLIC_FRONTEND_URL", "http://localhost:3000") + "/invite-profile-completion"
                
                invite_response = supabase.auth.admin.invite_user_by_email(
                    invitation.email,
                    options={
                        "redirect_to": redirect_to
                    }
                )
                
                logger.info(f"Supabase resend response: {invite_response}")
                
                # Update sent_at timestamp
                invitation.sent_at = now
                
                # If invitation was expired or close to expiring, extend expiration by 7 days
                if is_expired or (expires_at - now).days < 1:
                    invitation.expires_at = now + timedelta(days=7)
                    logger.info(f"Extended expiration date for invitation {invitation_id}")
                
                self.db.commit()
                self.db.refresh(invitation)
                
                logger.info(f"Successfully resent invitation {invitation_id} to {invitation.email}")
                return (True, "Invitation resent successfully")
                
            except AuthApiError as e:
                logger.error(f"Supabase API error when resending invitation {invitation_id}: {str(e)}")
                # Handle specific Supabase errors
                error_message = str(e)
                if "already exists" in error_message.lower() or "already registered" in error_message.lower():
                    # User already exists - this shouldn't happen for resend, but handle gracefully
                    logger.warning(f"User {invitation.email} already exists in Auth. Updating timestamp anyway.")
                    invitation.sent_at = now
                    if is_expired:
                        invitation.expires_at = now + timedelta(days=7)
                    self.db.commit()
                    return (True, "Invitation timestamp updated (user already exists)")
                else:
                    # Other Supabase errors (rate limits, network issues, etc.)
                    return (False, f"Failed to resend invitation: {error_message}")
                    
            except Exception as e:
                logger.error(f"Unexpected error when resending invitation {invitation_id}: {str(e)}")
                return (False, f"Failed to resend invitation: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error in resend_invitation for {invitation_id}: {str(e)}")
            return (False, f"Error resending invitation: {str(e)}")

# --- Add a dependency for this service ---
def get_invitation_service(
    db: Session = Depends(get_db)
) -> InvitationService:
    return InvitationService(db)
