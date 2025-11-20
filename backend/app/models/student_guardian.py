import uuid
import enum
from sqlalchemy import Column, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db import Base
from datetime import datetime, timezone

class GuardianRelationType(enum.Enum):
    primary = "primary"
    secondary = "secondary"
    emergency = "emergency"

class StudentGuardian(Base):
    __tablename__ = "student_guardians"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Organization-specific relationship
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    guardian_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    
    relationship_type = Column(Enum(GuardianRelationType), nullable=False, default=GuardianRelationType.primary)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))

    # Relationships
    organization = relationship("Organization", back_populates="student_guardian_links")
    student = relationship("Profile", foreign_keys=[student_id], back_populates="student_relationships")
    guardian = relationship("Profile", foreign_keys=[guardian_id], back_populates="guardian_relationships")
    
    __table_args__ = (
        UniqueConstraint('organization_id', 'student_id', 'guardian_id', name='_org_student_guardian_uc'),
    )
