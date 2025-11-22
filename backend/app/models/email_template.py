import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..db import Base


class EmailTemplate(Base):
    __tablename__ = "email_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True)
    
    # Template details
    name = Column(String, nullable=False)
    subject_template = Column(String, nullable=False)
    body_template = Column(Text, nullable=False)
    type = Column(String, nullable=False, index=True)  # referral, intervention, general
    scope = Column(String, nullable=False, index=True)  # organization, system
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="email_templates")
    creator = relationship("Profile", foreign_keys=[created_by_user_id], back_populates="created_email_templates")

