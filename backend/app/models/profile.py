import uuid
from sqlalchemy import Column, String
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
    
    # A user can be a member of many organizations
    memberships = relationship("OrganizationMember", back_populates="user_profile")
