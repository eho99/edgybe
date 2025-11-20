from sqlalchemy.orm import Session
from pydantic import EmailStr, UUID4
from fastapi import Depends, HTTPException
from supabase_auth.errors import AuthApiError
import logging
from datetime import datetime, timedelta, timezone

from .. import models
from .. import schemas
from ..db import get_db
# Import the admin client from existing auth file
from ..auth import supabase  

logger = logging.getLogger(__name__)

class InvitationService:
    def __init__(self, db: Session):
        self.db = db

    def _find_user_in_supabase(self, email: EmailStr):
        """
        Find a user in Supabase Auth by email.
        
        Returns:
            User object if found, None otherwise
        """
        logger.info(f"Checking if user {email} exists in Supabase Auth")
        users_response = supabase.auth.admin.list_users()  # TODO: this is inefficient to index in O(n)
        
        if not users_response:
            logger.info(f"No users found in Supabase Auth response for {email}")
            return None
        
        # Handle different response formats: list directly or response object with .users/.data
        users_list = None
        if isinstance(users_response, list):
            # Direct list of User objects
            users_list = users_response
        elif hasattr(users_response, 'users') and users_response.users:
            # Response object with .users attribute
            users_list = users_response.users
        elif hasattr(users_response, 'data') and users_response.data:
            # Response object with .data attribute
            users_list = users_response.data
        
        if not users_list:
            logger.info(f"Users list is empty for {email}")
            return None
        
        # Search for user by email
        for user in users_list:
            # Get email attribute - handle both string attributes and MagicMock
            user_email = getattr(user, 'email', None)
            if user_email == email:
                logger.info(f"Found user {email} in Supabase Auth")
                return user
        
        logger.info(f"User {email} not found in Supabase Auth")
        return None

    def _handle_existing_user(self, existing_user, email: EmailStr, full_name: str | None) -> tuple[UUID4, models.Profile]:
        """
        Handle the case where user exists in Supabase Auth.
        Ensures profile exists and is marked as completed.
        
        Returns:
            Tuple of (user_id, profile)
        """
        user_id = existing_user.id
        # Convert to UUID if it's a string (Supabase returns string UUIDs)
        if isinstance(user_id, str):
            from uuid import UUID
            user_id = UUID(user_id)
        
        logger.info(f"User {email} found in Auth with ID: {user_id}")
        
        # Get or create profile
        profile = self.db.query(models.Profile).filter(
            models.Profile.id == user_id
        ).first()
        
        if not profile:
            # User is in auth but not our DB? (Edge case - likely reactivation scenario)
            logger.warning(f"User {email} exists in Auth but not in Profile DB. Creating profile with completed status.")
            profile = self._create_local_profile(
                user_id=user_id,
                full_name=full_name or getattr(existing_user, 'email', email),
                has_completed_profile=True  # Existing users should be marked as completed
            )
        else:
            # Profile exists - ensure it's marked as completed for reactivated users
            if not profile.has_completed_profile:
                logger.info(f"User {email} has existing profile with incomplete status. Marking as completed for reactivation.")
                profile.has_completed_profile = True
            if full_name and not profile.full_name:
                profile.full_name = full_name
        
        return user_id, profile

    def _handle_new_user(self, email: EmailStr, org_id: UUID4, role: models.OrgRole, inviter_id: UUID4 | None) -> models.OrganizationMember:
        """
        Handle the case where user does NOT exist in Supabase Auth.
        Sends invitation and creates pending membership.
        
        Returns:
            OrganizationMember with user_id=None (pending invitation)
        """
        logger.info(f"User {email} not found in Auth. Inviting...")
        
        # Check if there's already a membership with this invite_email
        existing_member = self.db.query(models.OrganizationMember).filter(
            models.OrganizationMember.organization_id == org_id,
            models.OrganizationMember.invite_email == email
        ).first()
        
        if existing_member:
            logger.info(f"Membership with invite_email {email} already exists. Updating role if needed.")
            if existing_member.role != role:
                existing_member.role = role
                self.db.commit()
                self.db.refresh(existing_member)
            return existing_member
        
        # Send invitation via Supabase
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
            inviter_id=inviter_id,
            status=models.InvitationStatus.pending
        )
        self.db.add(invitation)
        
        # Create pending membership tied to invite_email (user_id will be set when they accept)
        member = models.OrganizationMember(
            organization_id=org_id,
            user_id=None,  # unknown until the user signs up
            invite_email=email,  # used to link after acceptance
            role=role,
            status=models.MemberStatus.active  # Active by default, they just need to accept
        )
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        self.db.refresh(invitation)
        
        logger.info(f"Invitation sent to {email}. Created invitation record and pending organization membership. Will link on acceptance.")
        return member

    def _handle_organization_membership(self, user_id: UUID4, email: EmailStr, org_id: UUID4, role: models.OrgRole) -> models.OrganizationMember:
        """
        Handle organization membership for an existing user.
        Either reactivates inactive membership, updates role, or creates new membership.
        
        Returns:
            OrganizationMember
        """
        # Check if user is already in the organization
        member = self.db.query(models.OrganizationMember).filter(
            models.OrganizationMember.user_id == user_id,
            models.OrganizationMember.organization_id == org_id
        ).first()

        if member:
            # User is already in org
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
            # User is not in org. Add them.
            logger.info(f"Adding new user {email} to org {org_id} with role {role}.")
            member = models.OrganizationMember(
                organization_id=org_id,
                user_id=user_id,
                role=role,
                status=models.MemberStatus.active
            )
            self.db.add(member)

        return member

    async def invite_or_add_user_to_org(
        self,
        org_id: UUID4,
        email: EmailStr,
        role: models.OrgRole,
        full_name: str | None = None,
        inviter_id: UUID4 | None = None
    ) -> models.OrganizationMember:
        """
        Main service function to invite or add a user to an organization.
        
        Flow:
        1. Check if user exists in Supabase Auth
        2a. If NOT found: Send invitation, create pending membership (returns early)
        2b. If found: Get/create profile, then handle organization membership
        3. Return the membership record
        
        Returns:
            OrganizationMember (either pending with user_id=None, or active with user_id set)
        """
        try:
            existing_user = self._find_user_in_supabase(email)
            
            if not existing_user:
                return self._handle_new_user(email, org_id, role, inviter_id)
            
            user_id, profile = self._handle_existing_user(existing_user, email, full_name)
            
            member = self._handle_organization_membership(user_id, email, org_id, role)
            
            self.db.commit()
            self.db.refresh(member)
            if profile:
                self.db.refresh(profile)
            
            return member
            
        except HTTPException:
            # Re-raise HTTPExceptions as-is
            self.db.rollback()
            raise
        except Exception as e:
            logger.error(f"Error in invitation process for {email}: {str(e)}")
            self.db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Failed to process invitation for {email}: {str(e)}"
            ) from e

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

    async def bulk_invite_users(
        self,
        org_id: UUID4,
        users: list[schemas.UserInviteRequest],
        inviter_id: UUID4 | None = None
    ) -> dict:
        """
        Bulk invite or add multiple users to an organization.
        
        Args:
            org_id: Organization ID
            users: List of UserInviteRequest objects
            inviter_id: ID of the user sending invitations
            
        Returns:
            Dict with 'successful', 'failed', 'total', 'succeeded', 'failed_count'
        """
        results = []
        errors = []
        
        print(f"[bulk_invite_users] users: {users}")
        
        for idx, user_data in enumerate(users):
            print(f"[bulk_invite_users] user_data: {user_data}")
            try:
                # Validate role is an internal role (not student/guardian)
                # Handle both enum and string comparisons
                role_value = user_data.role.value if hasattr(user_data.role, 'value') else str(user_data.role)
                if role_value in ['student', 'guardian'] or user_data.role in [models.OrgRole.student, models.OrgRole.guardian]:
                    errors.append({
                        "index": idx,
                        "email": user_data.email,
                        "error": f"Role '{role_value}' is not allowed for bulk invitations. Use student/guardian creation endpoints instead."
                    })
                    continue
                
                # Ensure database session is in a clean state before each invitation
                try:
                    self.db.rollback()
                except Exception:
                    pass  # Ignore rollback errors if session is already clean
                
                member = await self.invite_or_add_user_to_org(
                    org_id=org_id,
                    email=user_data.email,
                    role=user_data.role,
                    full_name=user_data.full_name,
                    inviter_id=inviter_id
                )

                print(f"[bulk_invite_users] member: {member}")
                
                # Convert member to dict for serialization
                # Ensure all fields are properly serialized
                try:
                    # Safely get role value
                    role_value = None
                    if member.role:
                        role_value = member.role.value if hasattr(member.role, 'value') else str(member.role)
                    
                    # Safely get status value
                    status_value = None
                    if member.status:
                        status_value = member.status.value if hasattr(member.status, 'value') else str(member.status)

                    print(f"[bulk_invite_users] role_value: {role_value}")
                    print(f"[bulk_invite_users] status_value: {status_value}")
                    
                    member_dict = {
                        "organization_id": str(member.organization_id),
                        "user_id": str(member.user_id) if member.user_id else None,
                        "invite_email": getattr(member, 'invite_email', None),
                        "role": role_value,
                        "status": status_value
                    }

                    print(f"[bulk_invite_users] member_dict: {member_dict}")
                    
                    results.append({
                        "email": user_data.email,
                        "member": member_dict,
                        "status": "success"
                    })
                except Exception as serialization_error:
                    # If serialization fails, add to errors instead
                    logger.error(f"Failed to serialize member for {user_data.email}: {str(serialization_error)}")
                    errors.append({
                        "index": idx,
                        "email": user_data.email,
                        "error": f"Failed to serialize response: {str(serialization_error)}"
                    })
            except HTTPException as e:
                # HTTPException has a detail attribute
                error_msg = str(e.detail) if hasattr(e, 'detail') and e.detail else str(e)
                errors.append({
                    "index": idx,
                    "email": user_data.email,
                    "error": error_msg
                })
                logger.warning(f"Failed to invite user at index {idx} ({user_data.email}): {error_msg}")
            except Exception as e:
                error_msg = str(e)
                # Clean up error message if it's too verbose
                if "Failed to process invitation" in error_msg:
                    # Extract the actual error from the wrapped exception
                    error_msg = error_msg.split(": ", 1)[-1] if ": " in error_msg else error_msg
                errors.append({
                    "index": idx,
                    "email": user_data.email,
                    "error": error_msg
                })
                logger.warning(f"Failed to invite user at index {idx} ({user_data.email}): {error_msg}")
        
        print(f"[bulk_invite_users] errors: {errors}")
        print(f"[bulk_invite_users] results: {results}")
        if errors and not results:
            # If all failed, raise an HTTPException
            error_summary = "; ".join([f"{e.get('email', 'unknown')}: {e.get('error', 'unknown error')}" for e in errors[:5]])
            if len(errors) > 5:
                error_summary += f" ... and {len(errors) - 5} more"
            raise HTTPException(
                status_code=400,
                detail=f"Failed to invite any users. Errors: {error_summary}"
            )
        
        return {
            "successful": results,
            "failed": errors,
            "total": len(users),
            "succeeded": len(results),
            "failed_count": len(errors)
        }

# --- Add a dependency for this service ---
def get_invitation_service(
    db: Session = Depends(get_db)
) -> InvitationService:
    return InvitationService(db)
