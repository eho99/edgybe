import uuid
import enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, UniqueConstraint, ForeignKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .db import Base

class OrgRole(enum.Enum):
    admin = "admin"
    member = "member"
    viewer = "viewer"

class MemberStatus(enum.Enum):
    active = "active"
    inactive = "inactive"

class Organization(Base):
    __tablename__ = "organizations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    members = relationship("OrganizationMember", back_populates="organization")

class Profile(Base):
    __tablename__ = "profiles"
    # This ID comes directly from supabase.auth.users.id
    # Note: We don't create a foreign key constraint here because auth.users
    # is managed by Supabase Auth and not part of our application schema
    id = Column(UUID(as_uuid=True), primary_key=True)
    full_name = Column(String)
    
    # A user can be a member of many organizations
    memberships = relationship("OrganizationMember", back_populates="user_profile")

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

