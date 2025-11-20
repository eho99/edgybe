from pydantic import BaseModel, UUID4, EmailStr
from typing import Optional
from ..models.student_guardian import GuardianRelationType
from .user import ProfileSchema

class GuardianLinkRequest(BaseModel):
    guardian_id: UUID4
    student_id: UUID4
    relationship_type: GuardianRelationType = GuardianRelationType.primary

class GuardianLinkResponse(BaseModel):
    id: UUID4
    organization_id: UUID4
    student_id: UUID4
    guardian_id: UUID4
    student: ProfileSchema
    guardian: ProfileSchema
    relationship_type: GuardianRelationType

    class Config:
        orm_mode = True

class StudentWithGuardiansResponse(BaseModel):
    student: ProfileSchema
    guardians: list[GuardianLinkResponse]

class GuardianWithStudentsResponse(BaseModel):
    guardian: ProfileSchema
    students: list[GuardianLinkResponse]

# Schemas for profile creation
class CreateStudentRequest(BaseModel):
    full_name: str
    email: Optional[str] = None

class CreateGuardianRequest(BaseModel):
    full_name: str
    email: Optional[str] = None

class StudentData(BaseModel):
    full_name: str
    email: Optional[str] = None

class GuardianData(BaseModel):
    full_name: str
    email: Optional[str] = None

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
