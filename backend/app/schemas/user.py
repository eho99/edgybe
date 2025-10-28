from pydantic import BaseModel, EmailStr, UUID4, Field, field_validator
from ..models.organization_member import OrgRole

# Schemas for inviting a new user
class UserInvite(BaseModel):
    email: EmailStr
    role: OrgRole = OrgRole.staff

# New schemas for invitation and profile management
class UserInviteRequest(BaseModel):
    email: EmailStr
    full_name: str | None = None
    role: OrgRole = OrgRole.staff

class ProfileSchema(BaseModel):
    id: UUID4
    full_name: str | None
    has_completed_profile: bool = Field(default=False)

    class Config:
        orm_mode = True
    
    @field_validator('has_completed_profile', mode='before')
    @classmethod
    def handle_none_has_completed_profile(cls, v):
        """Convert None to False for has_completed_profile field."""
        return False if v is None else v

class ProfileUpdateSchema(BaseModel):
    full_name: str
