from pydantic import BaseModel, EmailStr, UUID4
from datetime import datetime
from .models import OrgRole, MemberStatus

class OrganizationBase(BaseModel):
    name: str

class OrganizationCreate(OrganizationBase):
    pass

class Organization(OrganizationBase):
    id: UUID4
    created_at: datetime

    class Config:
        orm_mode = True

# Schemas for inviting a new user
class UserInvite(BaseModel):
    email: EmailStr
    role: OrgRole = OrgRole.member

# Schemas for the user we get back from Supabase
class SupabaseUser(BaseModel):
    id: UUID4
    email: EmailStr
    
class AuthenticatedMember(BaseModel):
    user: SupabaseUser
    org_id: UUID4
    role: OrgRole

