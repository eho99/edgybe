from pydantic import BaseModel, UUID4, EmailStr
from datetime import datetime
from typing import Optional
from ..models.organization_member import OrgRole, MemberStatus

class AccountResponse(BaseModel):
    id: UUID4
    organization_id: UUID4
    user_id: UUID4 | None
    invite_email: str | None = None
    email: EmailStr | None = None  # From Supabase Auth
    full_name: str | None = None  # From Profile
    role: OrgRole
    status: MemberStatus
    joined_at: datetime

    class Config:
        orm_mode = True

class AccountListResponse(BaseModel):
    accounts: list[AccountResponse]
    total: int
    page: int
    per_page: int
    total_pages: int

