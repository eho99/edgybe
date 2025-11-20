import uuid
from sqlalchemy import Column, String, DateTime, Integer, Index
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db import Base

class Organization(Base):
    __tablename__ = "organizations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # District relationship (for future use)
    district_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Address fields
    street_number = Column(String, nullable=True)
    street_name = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    zip_code = Column(String, nullable=True)
    
    # Contact information
    phone_number = Column(String, nullable=True)
    office_extension = Column(String, nullable=True)
    
    # Grade range
    lower_grade = Column(Integer, nullable=True)
    upper_grade = Column(Integer, nullable=True)
    
    # URL-friendly identifier
    slug = Column(String, nullable=True, unique=True, index=True)
    
    # Configuration fields (JSON)
    preset_config = Column(JSON, nullable=True)
    form_config = Column(JSON, nullable=True)
    
    # SIS integration fields
    aeries_school_code = Column(String, nullable=True, index=True)
    sis_source_id = Column(String, nullable=True, index=True)
    sis_client_id = Column(String, nullable=True)
    sis_client_secret = Column(String, nullable=True)
    
    # Additional fields
    disclaimers = Column(JSON, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    members = relationship("OrganizationMember", back_populates="organization")
    student_guardian_links = relationship("StudentGuardian", back_populates="organization")
    invitations = relationship("Invitation", back_populates="organization")
