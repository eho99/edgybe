from pydantic import BaseModel, UUID4, EmailStr, Field, field_validator, ConfigDict
from typing import Optional
from pydantic_extra_types.phone_numbers import PhoneNumber
from ..models.student_guardian import GuardianRelationType
from .user import ProfileSchema

class GuardianLinkRequest(BaseModel):
    guardian_id: UUID4
    student_id: UUID4
    relationship_type: GuardianRelationType = GuardianRelationType.primary

class GuardianLinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    organization_id: UUID4
    student_id: UUID4
    guardian_id: UUID4
    student: ProfileSchema
    guardian: ProfileSchema
    guardian_email: Optional[EmailStr] = None
    relationship_type: GuardianRelationType

class StudentWithGuardiansResponse(BaseModel):
    student: ProfileSchema
    guardians: list[GuardianLinkResponse]

class GuardianWithStudentsResponse(BaseModel):
    guardian: ProfileSchema
    students: list[GuardianLinkResponse]

# Schemas for profile creation
class CreateStudentRequest(BaseModel):
    full_name: str
    grade_level: str = Field(..., description="Grade level is required for students")
    student_id: str = Field(..., description="Student ID is required for students")
    email: Optional[str] = None
    phone: Optional[PhoneNumber] = None
    street_number: Optional[str] = None
    street_name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    preferred_language: Optional[str] = None
    
    @field_validator('phone', mode='before')
    @classmethod
    def handle_empty_phone(cls, v):
        """Convert empty strings to None for phone field."""
        if v == '' or v is None:
            return None
        return v

class CreateGuardianRequest(BaseModel):
    full_name: str
    email: EmailStr = Field(..., description="Email is required for guardians")
    phone: Optional[PhoneNumber] = None
    street_number: Optional[str] = None
    street_name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    preferred_language: Optional[str] = None
    
    @field_validator('phone', mode='before')
    @classmethod
    def handle_empty_phone(cls, v):
        """Convert empty strings to None for phone field."""
        if v == '' or v is None:
            return None
        return v

class StudentData(BaseModel):
    full_name: str
    grade_level: str = Field(..., description="Grade level is required for students")
    student_id: str = Field(..., description="Student ID is required for students")
    email: Optional[str] = None
    phone: Optional[PhoneNumber] = None
    street_number: Optional[str] = None
    street_name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    preferred_language: Optional[str] = None
    
    @field_validator('phone', mode='before')
    @classmethod
    def handle_empty_phone(cls, v):
        """Convert empty strings to None for phone field."""
        if v == '' or v is None:
            return None
        return v

class GuardianData(BaseModel):
    full_name: str
    email: EmailStr = Field(..., description="Email is required for guardians")
    phone: Optional[PhoneNumber] = None
    street_number: Optional[str] = None
    street_name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    preferred_language: Optional[str] = None
    
    @field_validator('phone', mode='before')
    @classmethod
    def handle_empty_phone(cls, v):
        """Convert empty strings to None for phone field."""
        if v == '' or v is None:
            return None
        return v

class StudentGuardianPair(BaseModel):
    student: StudentData
    guardian: GuardianData
    relationship_type: Optional[GuardianRelationType] = GuardianRelationType.primary

class BulkCreateStudentsRequest(BaseModel):
    students: list[StudentData]

class BulkCreateGuardiansRequest(BaseModel):
    guardians: list[GuardianData]

class BulkCreatePairsRequest(BaseModel):
    pairs: list[StudentGuardianPair]

class BulkCreateResponse(BaseModel):
    created: int
    profiles: list[ProfileSchema]

class BulkCreatePairsResponse(BaseModel):
    created: int
    pairs: list[dict]  # Each dict has student_profile, guardian_profile, link

class ProfileListResponse(BaseModel):
    profiles: list[ProfileSchema]
    total: int
    page: int
    per_page: int
    total_pages: int
