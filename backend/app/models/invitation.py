import uuid
import enum
from sqlalchemy import Column, DateTime, ForeignKey, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db import Base
from .organization_member import OrgRole

class InvitationStatus(enum.Enum):
    pending = "pending"
    accepted = "accepted"
    expired = "expired"
    cancelled = "cancelled"

class Invitation(Base):
    __tablename__ = "invitations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Organization this invitation is for
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    
    # Invitation details
    email = Column(String(255), nullable=False)
    role = Column(Enum(OrgRole, create_type=False), nullable=False)
    
    # Who sent the invitation
    inviter_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    
    # Status and timing
    status = Column(Enum(InvitationStatus), nullable=False, default=InvitationStatus.pending)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), server_default=func.now() + func.interval('7 days'))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="invitations")
    inviter = relationship("Profile", back_populates="sent_invitations")
    
    def __repr__(self):
        return f"<Invitation(id={self.id}, email={self.email}, status={self.status.value})>"
