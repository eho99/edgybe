from pydantic import BaseModel, EmailStr, UUID4, Field, field_validator
from typing import Optional
from datetime import datetime
from pydantic_extra_types.phone_numbers import PhoneNumber
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

class BulkUserInviteRequest(BaseModel):
    users: list[UserInviteRequest]

class BulkInviteResponse(BaseModel):
    successful: list[dict]
    failed: list[dict]
    total: int
    succeeded: int
    failed_count: int

class ProfileSchema(BaseModel):
    id: UUID4
    full_name: str | None
    has_completed_profile: bool = Field(default=False)
    phone: Optional[PhoneNumber] = None
    street_number: Optional[str] = None
    street_name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    preferred_language: Optional[str] = None
    grade_level: Optional[str] = None
    student_id: Optional[str] = None
    is_active: bool = Field(default=True)
    updated_at: datetime

    class Config:
        orm_mode = True
    
    @field_validator('has_completed_profile', mode='before')
    @classmethod
    def handle_none_has_completed_profile(cls, v):
        """Convert None to False for has_completed_profile field."""
        return False if v is None else v
    
    @field_validator('is_active', mode='before')
    @classmethod
    def handle_none_is_active(cls, v):
        """Convert None to True for is_active field."""
        return True if v is None else v
    
class ProfileUpdateSchema(BaseModel):
    """Schema for updating profile - all fields optional."""
    full_name: Optional[str] = None
    phone: Optional[PhoneNumber] = None
    street_number: Optional[str] = None
    street_name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    preferred_language: Optional[str] = None
    grade_level: Optional[str] = None
    student_id: Optional[str] = None
    is_active: Optional[bool] = None
    
    @field_validator('phone', mode='before')
    @classmethod
    def handle_empty_phone(cls, v):
        """Convert empty strings to None for phone field."""
        if v == '' or v is None:
            return None
        return v
