import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship

from ..db import Base


class Referral(Base):
    __tablename__ = "referrals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_admin_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Referral details
    status = Column(String, nullable=False)  # DRAFT, SUBMITTED, REVIEW, CLOSED
    type = Column(String, nullable=False, index=True)  # Behavior, Support, etc.
    location = Column(String, nullable=True)
    time_of_day = Column(String, nullable=True)
    behaviors = Column(JSON, nullable=True)  # JSONB array of strings
    description = Column(Text, nullable=True)
    
    # Archiving
    archived = Column(Boolean, nullable=False, default=False, index=True)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="referrals")
    student = relationship("Profile", foreign_keys=[student_id], back_populates="student_referrals")
    author = relationship("Profile", foreign_keys=[author_id], back_populates="authored_referrals")
    assigned_admin = relationship("Profile", foreign_keys=[assigned_admin_id], back_populates="assigned_referrals")
    interventions = relationship("Intervention", back_populates="referral", cascade="all, delete-orphan")
    communication_logs = relationship("CommunicationLog", back_populates="referral", cascade="all, delete-orphan")


class Intervention(Base):
    __tablename__ = "interventions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    referral_id = Column(UUID(as_uuid=True), ForeignKey("referrals.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True)
    
    # Intervention details
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, index=True)  # PLANNED, IN_PROGRESS, COMPLETED
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    referral = relationship("Referral", back_populates="interventions")
    creator = relationship("Profile", foreign_keys=[created_by], back_populates="created_interventions")


class CommunicationLog(Base):
    __tablename__ = "communication_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    referral_id = Column(UUID(as_uuid=True), ForeignKey("referrals.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Communication details
    communication_type = Column(String, nullable=False)  # email, phone, in_person
    recipient_email = Column(String, nullable=False)
    subject = Column(String, nullable=True)
    status = Column(String, nullable=False)  # sent, failed, pending
    error_message = Column(Text, nullable=True)
    
    # Timestamp
    sent_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    
    # Relationship
    referral = relationship("Referral", back_populates="communication_logs")

