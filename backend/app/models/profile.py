import uuid
from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..db import Base

class Profile(Base):
    __tablename__ = "profiles"
    # This ID comes directly from supabase.auth.users.id
    # Note: We don't create a foreign key constraint here because auth.users
    # is managed by Supabase Auth and not part of our application schema
    id = Column(UUID(as_uuid=True), primary_key=True)
    full_name = Column(String)
    has_completed_profile = Column(Boolean, nullable=True, default=False)
    
    # A user can be a member of many organizations
    memberships = relationship("OrganizationMember", back_populates="user_profile")
    
    # Student-Guardian relationships (as student)
    student_relationships = relationship("StudentGuardian", foreign_keys="StudentGuardian.student_id", back_populates="student")
    
    # Student-Guardian relationships (as guardian)
    guardian_relationships = relationship("StudentGuardian", foreign_keys="StudentGuardian.guardian_id", back_populates="guardian")
    
    # Invitations sent by this user
    sent_invitations = relationship("Invitation", back_populates="inviter")