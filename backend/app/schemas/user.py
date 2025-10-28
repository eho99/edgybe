from pydantic import BaseModel, EmailStr
from ..models.organization_member import OrgRole

# Schemas for inviting a new user
class UserInvite(BaseModel):
    email: EmailStr
    role: OrgRole = OrgRole.staff
