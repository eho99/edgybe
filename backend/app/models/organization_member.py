import uuid
import enum
from sqlalchemy import Column, DateTime, ForeignKey, Enum, UniqueConstraint, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db import Base
from datetime import datetime, timezone

class OrgRole(enum.Enum):
    admin = "admin"
    secretary = "secretary"
    staff = "staff"
    guardian = "guardian"
    student = "student"

class MemberStatus(enum.Enum):
    active = "active"
    inactive = "inactive"

class OrganizationMember(Base):
    __tablename__ = "organization_members"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    # Allow null user_id for email-based invitations before the user signs up
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=True)
    # Store invite email for pending invitations until linked to a real user
    invite_email = Column(String, nullable=True, index=True)
    
    role = Column(Enum(OrgRole, create_type=False), nullable=False, default=OrgRole.staff)
    status = Column(Enum(MemberStatus), nullable=False, default=MemberStatus.active)
    
    joined_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))

    organization = relationship("Organization", back_populates="members")
    user_profile = relationship("Profile", back_populates="memberships")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Automatically set status based on role
        if self.role in [OrgRole.guardian, OrgRole.student]:
            self.status = MemberStatus.inactive
        else:
            self.status = MemberStatus.active
    
    __table_args__ = (
        UniqueConstraint('organization_id', 'user_id', name='_org_user_uc'),
    )
