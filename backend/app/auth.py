import os
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from supabase import create_client, Client
from supabase_auth.errors import AuthApiError
from . import schemas
from .db import get_db
from .models import OrganizationMember, MemberStatus
from sqlalchemy.orm import Session
from pydantic import UUID4

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")


# Create a single, reusable Supabase admin client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # We don't use tokenUrl, but it's needed

async def get_current_user(request: Request) -> schemas.SupabaseUser:
    """Dependency to get the user from Supabase JWT."""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    token = auth_header.replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=401, detail="Invalid token format")

    try:
        user_response = supabase.auth.get_user(token)
        user = user_response.user
        if not user:
             raise HTTPException(status_code=401, detail="Invalid token or user not found")
        
        return schemas.SupabaseUser(id=user.id, email=user.email)
    
    except AuthApiError as e:
        raise HTTPException(status_code=401, detail=f"Authentication error: {e.message}")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

async def get_current_active_member(
    request: Request,
    org_id: UUID4,
    db: Session = Depends(get_db),
    user: schemas.SupabaseUser = Depends(get_current_user)
) -> schemas.AuthenticatedMember:
    """
    Dependency that verifies the user is an *active member* of the
    organization specified in the path.
    """
    try:
        member = db.query(OrganizationMember).filter(
            OrganizationMember.user_id == user.id,
            OrganizationMember.organization_id == org_id
        ).first()

        if not member:
            raise HTTPException(status_code=403, detail="User not a member of this organization")
        
        if member.status != MemberStatus.active:
            raise HTTPException(status_code=403, detail="User is inactive in this organization")

        return schemas.AuthenticatedMember(
            user=user,
            org_id=member.organization_id,
            role=member.role
        )
    except Exception as e:
        raise HTTPException(status_code=403, detail=f"Access denied: {str(e)}")

