import uuid
import enum
from sqlalchemy import Column, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db import Base

class OrgRole(enum.Enum):
    admin = "admin"
    member = "member"
    viewer = "viewer"

class MemberStatus(enum.Enum):
    active = "active"
    inactive = "inactive"

class OrganizationMember(Base):
    __tablename__ = "organization_members"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    
    role = Column(Enum(OrgRole), nullable=False, default=OrgRole.member)
    status = Column(Enum(MemberStatus), nullable=False, default=MemberStatus.active)
    
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    organization = relationship("Organization", back_populates="members")
    user_profile = relationship("Profile", back_populates="memberships")
    
    __table_args__ = (
        UniqueConstraint('organization_id', 'user_id', name='_org_user_uc'),
    )
