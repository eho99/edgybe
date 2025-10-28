from pydantic import BaseModel, UUID4
from datetime import datetime

class OrganizationBase(BaseModel):
    name: str

class OrganizationCreate(OrganizationBase):
    pass

class Organization(OrganizationBase):
    id: UUID4
    created_at: datetime

    class Config:
        orm_mode = True
