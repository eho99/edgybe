from pydantic import BaseModel, UUID4
from datetime import datetime
from ..models.organization_member import OrgRole

class OrganizationMembership(BaseModel):
    org_id: UUID4
    role: OrgRole
    organization_name: str
    joined_at: datetime

    class Config:
        orm_mode = True
