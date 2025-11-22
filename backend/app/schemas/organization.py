from pydantic import BaseModel, UUID4, Field, model_validator
from datetime import datetime
from typing import Optional
from pydantic_extra_types.phone_numbers import PhoneNumber

class OrganizationBase(BaseModel):
    name: str
    street_number: Optional[str] = None
    street_name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    phone_number: Optional[PhoneNumber] = None
    office_extension: Optional[str] = None
    lower_grade: Optional[int] = Field(None, ge=0, le=12)
    upper_grade: Optional[int] = Field(None, ge=0, le=12)
    slug: Optional[str] = None
    preset_config: Optional[dict] = None
    form_config: Optional[dict] = None
    aeries_school_code: Optional[str] = None
    sis_source_id: Optional[str] = None
    sis_client_id: Optional[str] = None
    sis_client_secret: Optional[str] = None
    disclaimers: Optional[dict] = None
    
    @model_validator(mode='after')
    def validate_grade_range(self):
        """Ensure lower_grade <= upper_grade if both are provided."""
        if self.lower_grade is not None and self.upper_grade is not None:
            if self.lower_grade > self.upper_grade:
                raise ValueError('lower_grade must be less than or equal to upper_grade')
        return self

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationUpdate(BaseModel):
    """Schema for updating organization - all fields optional."""
    name: Optional[str] = None
    street_number: Optional[str] = None
    street_name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    phone_number: Optional[PhoneNumber] = None
    office_extension: Optional[str] = None
    lower_grade: Optional[int] = Field(None, ge=0, le=12)
    upper_grade: Optional[int] = Field(None, ge=0, le=12)
    slug: Optional[str] = None
    preset_config: Optional[dict] = None
    form_config: Optional[dict] = None
    aeries_school_code: Optional[str] = None
    sis_source_id: Optional[str] = None
    sis_client_id: Optional[str] = None
    sis_client_secret: Optional[str] = None
    disclaimers: Optional[dict] = None
    
    @model_validator(mode='after')
    def validate_grade_range(self):
        """Ensure lower_grade <= upper_grade if both are provided."""
        if self.lower_grade is not None and self.upper_grade is not None:
            if self.lower_grade > self.upper_grade:
                raise ValueError('lower_grade must be less than or equal to upper_grade')
        return self

class Organization(OrganizationBase):
    id: UUID4
    district_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
