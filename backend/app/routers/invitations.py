from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import UUID4
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import Optional

from .. import models, schemas, auth
from ..db import get_db
from ..services.invitations import InvitationService, get_invitation_service

router = APIRouter(
    prefix="/api/v1/organizations/{org_id}/invitations",
    tags=["Invitations"],
)

@router.get(
    "/",
    response_model=schemas.InvitationListResponse
)
async def list_invitations(
    org_id: UUID4,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    status_filter: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    admin_member: schemas.AuthenticatedMember = Depends(auth.require_admin_role)
):
    """
    List all invitations for an organization with pagination and filtering.
    Only Admins can perform this action.
    """
    try:
        # Build query
        query = db.query(models.Invitation).filter(
            models.Invitation.organization_id == org_id
        )
        
        # Apply status filter
        if status_filter:
            try:
                status_enum = models.InvitationStatus(status_filter)
                query = query.filter(models.Invitation.status == status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status filter: {status_filter}"
                )
        
        # Apply search filter
        if search:
            query = query.filter(
                or_(
                    models.Invitation.email.ilike(f"%{search}%"),
                    models.Profile.full_name.ilike(f"%{search}%")
                )
            ).join(models.Profile, models.Invitation.inviter_id == models.Profile.id)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        invitations = query.offset(offset).limit(per_page).all()
        
        # Convert to response format
        invitation_responses = []
        for invitation in invitations:
            # Get inviter name
            inviter = db.query(models.Profile).filter(
                models.Profile.id == invitation.inviter_id
            ).first()
            
            invitation_responses.append(schemas.InvitationResponse(
                id=invitation.id,
                organization_id=invitation.organization_id,
                email=invitation.email,
                role=invitation.role,
                inviter_id=invitation.inviter_id,
                status=invitation.status,
                sent_at=invitation.sent_at,
                accepted_at=invitation.accepted_at,
                expires_at=invitation.expires_at,
                created_at=invitation.created_at,
                updated_at=invitation.updated_at,
                inviter_name=inviter.full_name if inviter else None
            ))
        
        total_pages = (total + per_page - 1) // per_page
        
        return schemas.InvitationListResponse(
            invitations=invitation_responses,
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
            detail=f"Failed to list invitations: {str(e)}"
        )

@router.get(
    "/stats",
    response_model=schemas.InvitationStats
)
async def get_invitation_stats(
    org_id: UUID4,
    db: Session = Depends(get_db),
    admin_member: schemas.AuthenticatedMember = Depends(auth.require_admin_role)
):
    """
    Get invitation statistics for an organization.
    Only Admins can perform this action.
    """
    try:
        # Count invitations by status
        pending = db.query(models.Invitation).filter(
            and_(
                models.Invitation.organization_id == org_id,
                models.Invitation.status == models.InvitationStatus.pending
            )
        ).count()
        
        accepted = db.query(models.Invitation).filter(
            and_(
                models.Invitation.organization_id == org_id,
                models.Invitation.status == models.InvitationStatus.accepted
            )
        ).count()
        
        expired = db.query(models.Invitation).filter(
            and_(
                models.Invitation.organization_id == org_id,
                models.Invitation.status == models.InvitationStatus.expired
            )
        ).count()
        
        cancelled = db.query(models.Invitation).filter(
            and_(
                models.Invitation.organization_id == org_id,
                models.Invitation.status == models.InvitationStatus.cancelled
            )
        ).count()
        
        total = pending + accepted + expired + cancelled
        
        return schemas.InvitationStats(
            pending=pending,
            accepted=accepted,
            expired=expired,
            cancelled=cancelled,
            total=total
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get invitation stats: {str(e)}"
        )

@router.post(
    "/{invitation_id}/resend",
    response_model=schemas.InvitationResponse
)
async def resend_invitation(
    org_id: UUID4,
    invitation_id: UUID4,
    db: Session = Depends(get_db),
    admin_member: schemas.AuthenticatedMember = Depends(auth.require_admin_role),
    invitation_service: InvitationService = Depends(get_invitation_service)
):
    """
    Resend an invitation email via Supabase.
    Only Admins can perform this action.
    """
    try:
        # Use the service method to resend the invitation
        success, message = await invitation_service.resend_invitation(
            invitation_id=invitation_id,
            org_id=org_id
        )
        
        if not success:
            # Check if it's a "not found" error
            if "not found" in message.lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=message
                )
            # Check if it's a "wrong status" error
            elif "status" in message.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=message
                )
            # Other errors
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=message
                )
        
        # Fetch the updated invitation to return
        invitation = db.query(models.Invitation).filter(
            and_(
                models.Invitation.id == invitation_id,
                models.Invitation.organization_id == org_id
            )
        ).first()
        
        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found after resend"
            )
        
        # Get inviter name
        inviter = db.query(models.Profile).filter(
            models.Profile.id == invitation.inviter_id
        ).first()
        
        return schemas.InvitationResponse(
            id=invitation.id,
            organization_id=invitation.organization_id,
            email=invitation.email,
            role=invitation.role,
            inviter_id=invitation.inviter_id,
            status=invitation.status,
            sent_at=invitation.sent_at,
            accepted_at=invitation.accepted_at,
            expires_at=invitation.expires_at,
            created_at=invitation.created_at,
            updated_at=invitation.updated_at,
            inviter_name=inviter.full_name if inviter else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resend invitation: {str(e)}"
        )

@router.delete(
    "/{invitation_id}"
)
async def cancel_invitation(
    org_id: UUID4,
    invitation_id: UUID4,
    db: Session = Depends(get_db),
    admin_member: schemas.AuthenticatedMember = Depends(auth.require_admin_role)
):
    """
    Cancel an invitation.
    Only Admins can perform this action.
    """
    try:
        # Find the invitation
        invitation = db.query(models.Invitation).filter(
            and_(
                models.Invitation.id == invitation_id,
                models.Invitation.organization_id == org_id
            )
        ).first()
        
        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found"
            )
        
        if invitation.status != models.InvitationStatus.pending:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only cancel pending invitations"
            )
        
        # Mark as cancelled
        invitation.status = models.InvitationStatus.cancelled
        db.commit()
        
        return {"message": "Invitation cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel invitation: {str(e)}"
        )


