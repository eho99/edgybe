from pydantic import BaseModel, UUID4
from ..models.student_guardian import GuardianRelationType
from .user import ProfileSchema

class GuardianLinkRequest(BaseModel):
    guardian_id: UUID4
    student_id: UUID4
    relationship_type: GuardianRelationType = GuardianRelationType.primary

class GuardianLinkResponse(BaseModel):
    id: UUID4
    organization_id: UUID4
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
