import uuid
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db import Base
from datetime import datetime, timezone

class Profile(Base):
    __tablename__ = "profiles"
    # This ID comes directly from supabase.auth.users.id
    # Note: We don't create a foreign key constraint here because auth.users
    # is managed by Supabase Auth and not part of our application schema
    id = Column(UUID(as_uuid=True), primary_key=True)
    full_name = Column(String)
    has_completed_profile = Column(Boolean, nullable=True, default=False)
    
    # Contact information
    phone = Column(String, nullable=True)
    
    # Address fields
    street_number = Column(String, nullable=True)
    street_name = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    zip_code = Column(String, nullable=True)
    country = Column(String, nullable=True)
    
    # User preferences
    preferred_language = Column(String, nullable=True)
    
    # Student-specific fields
    grade_level = Column(String, nullable=True)
    student_id = Column(String, nullable=True, unique=True, index=True)
    
    # Status and timestamps
    is_active = Column(Boolean, nullable=True, default=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    # A user can be a member of many organizations
    memberships = relationship("OrganizationMember", back_populates="user_profile")
    
    # Student-Guardian relationships (as student)
    student_relationships = relationship("StudentGuardian", foreign_keys="StudentGuardian.student_id", back_populates="student")
    
    # Student-Guardian relationships (as guardian)
    guardian_relationships = relationship("StudentGuardian", foreign_keys="StudentGuardian.guardian_id", back_populates="guardian")

    # Invitations sent by this user
    sent_invitations = relationship("Invitation", back_populates="inviter")
    
    # Referrals relationships
    student_referrals = relationship("Referral", foreign_keys="Referral.student_id", back_populates="student")
    authored_referrals = relationship("Referral", foreign_keys="Referral.author_id", back_populates="author")
    created_interventions = relationship("Intervention", foreign_keys="Intervention.created_by", back_populates="creator")
    created_email_templates = relationship("EmailTemplate", foreign_keys="EmailTemplate.created_by_user_id", back_populates="creator")