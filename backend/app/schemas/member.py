from pydantic import BaseModel, UUID4
from ..models.organization_member import OrgRole, MemberStatus

class OrganizationMemberPublic(BaseModel):
    organization_id: UUID4
    user_id: UUID4 | None
    invite_email: str | None = None
    role: OrgRole
    status: MemberStatus

    class Config:
        orm_mode = True
