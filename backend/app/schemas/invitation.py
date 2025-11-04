from pydantic import BaseModel, EmailStr, UUID4, Field
from datetime import datetime
from typing import Optional
from ..models.organization_member import OrgRole
from ..models.invitation import InvitationStatus

class InvitationBase(BaseModel):
    email: EmailStr
    role: OrgRole

class InvitationCreate(InvitationBase):
    pass

class InvitationUpdate(BaseModel):
    status: Optional[InvitationStatus] = None

class InvitationResponse(InvitationBase):
    id: UUID4
    organization_id: UUID4
    inviter_id: UUID4
    status: InvitationStatus
    sent_at: datetime
    accepted_at: Optional[datetime] = None
    expires_at: datetime
    created_at: datetime
    updated_at: datetime
    
    # Include inviter details
    inviter_name: Optional[str] = None
    
    class Config:
        orm_mode = True

class InvitationListResponse(BaseModel):
    invitations: list[InvitationResponse]
    total: int
    page: int
    per_page: int
    total_pages: int

class InvitationStats(BaseModel):
    pending: int
    accepted: int
    expired: int
    cancelled: int
    total: int


