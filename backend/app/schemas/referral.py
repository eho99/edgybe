from pydantic import BaseModel, UUID4, Field
from datetime import datetime
from typing import Optional, List


# Configuration schemas
class ReferralConfigResponse(BaseModel):
    types: List[str]
    locations: dict
    time_of_day: dict
    behaviors: dict
    common_interventions: List[str]


# Referral schemas
class ReferralCreate(BaseModel):
    student_id: UUID4
    type: str
    location: Optional[str] = None
    time_of_day: Optional[str] = None
    behaviors: Optional[List[str]] = None
    description: Optional[str] = None


class ReferralUpdate(BaseModel):
    status: Optional[str] = None
    type: Optional[str] = None
    location: Optional[str] = None
    time_of_day: Optional[str] = None
    behaviors: Optional[List[str]] = None
    description: Optional[str] = None


class InterventionBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = Field(default="PLANNED")
    completed_at: Optional[datetime] = None


class InterventionCreate(InterventionBase):
    pass


class InterventionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    completed_at: Optional[datetime] = None


class InterventionResponse(InterventionBase):
    id: UUID4
    referral_id: UUID4
    created_by: Optional[UUID4] = None
    created_at: datetime
    updated_at: datetime
    creator_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class ReferralResponse(BaseModel):
    id: UUID4
    organization_id: UUID4
    student_id: UUID4
    author_id: Optional[UUID4] = None
    status: str
    type: str
    location: Optional[str] = None
    time_of_day: Optional[str] = None
    behaviors: Optional[List[str]] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Nested data
    student_name: Optional[str] = None
    student_student_id: Optional[str] = None
    student_grade_level: Optional[str] = None
    author_name: Optional[str] = None
    interventions: List[InterventionResponse] = []
    
    class Config:
        from_attributes = True


class ReferralListItem(BaseModel):
    id: UUID4
    organization_id: UUID4
    student_id: UUID4
    author_id: Optional[UUID4] = None
    status: str
    type: str
    location: Optional[str] = None
    time_of_day: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Nested data
    student_name: Optional[str] = None
    student_student_id: Optional[str] = None
    author_name: Optional[str] = None
    intervention_count: int = 0
    
    class Config:
        from_attributes = True


class ReferralListResponse(BaseModel):
    referrals: List[ReferralListItem]
    total: int
    page: int
    per_page: int
    total_pages: int


# Email request schema
class EmailRequest(BaseModel):
    recipient_emails: List[str]
    subject: Optional[str] = None
    message: Optional[str] = None
    template_id: Optional[UUID4] = None


class EmailSendResponse(BaseModel):
    success: bool
    message: str
    log_id: Optional[UUID4] = None

