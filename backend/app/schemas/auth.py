from pydantic import BaseModel, UUID4, EmailStr
from ..models.organization_member import OrgRole

# Schemas for the user we get back from Supabase
class SupabaseUser(BaseModel):
    id: UUID4
    email: EmailStr
    
class AuthenticatedMember(BaseModel):
    user: SupabaseUser
    org_id: UUID4
    role: OrgRole
