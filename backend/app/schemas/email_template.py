from pydantic import BaseModel, UUID4, Field
from datetime import datetime
from typing import Optional, List


class EmailTemplateCreate(BaseModel):
    name: str
    subject_template: str
    body_template: str
    type: str  # referral, intervention, general
    scope: str = Field(default="organization")  # organization, system
    is_active: bool = Field(default=True)


class EmailTemplateUpdate(BaseModel):
    name: Optional[str] = None
    subject_template: Optional[str] = None
    body_template: Optional[str] = None
    type: Optional[str] = None
    scope: Optional[str] = None
    is_active: Optional[bool] = None


class EmailTemplateResponse(BaseModel):
    id: UUID4
    organization_id: Optional[UUID4] = None
    created_by_user_id: Optional[UUID4] = None
    name: str
    subject_template: str
    body_template: str
    type: str
    scope: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # Additional fields
    creator_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class EmailTemplateListResponse(BaseModel):
    templates: List[EmailTemplateResponse]
    total: int
    page: int
    per_page: int
    total_pages: int

