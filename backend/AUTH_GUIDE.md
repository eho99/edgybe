# Authentication and Authorization Guide

This guide explains how to use the centralized authentication and authorization system for organization and role-based access control.

## Overview

The auth system provides:
- **Centralized org ID fetching** - Easy to get user's organizations
- **Role-based permissions** - Admin, Member, Viewer levels
- **Reusable dependencies** - Use across all endpoints
- **Database-level security** - All checks happen server-side

## Available Auth Dependencies

### Basic Authentication
```python
from ..auth import get_current_user

@router.get("/protected")
async def protected_endpoint(
    user: schemas.SupabaseUser = Depends(get_current_user)
):
    return {"user_id": user.id}
```

### Organization Access

#### Get User's Organizations
```python
from ..auth import get_user_organizations

@router.get("/my-orgs")
async def get_my_orgs(
    memberships: List[schemas.OrganizationMembership] = Depends(get_user_organizations)
):
    return memberships
```

#### Get User's Default Organization
```python
from ..auth import get_user_default_organization

@router.get("/my-default-org")
async def get_my_default_org(
    member: schemas.AuthenticatedMember = Depends(get_user_default_organization)
):
    return {"org_id": member.org_id, "role": member.role}
```

#### Organization-Specific Access
```python
from ..auth import get_current_active_member

@router.get("/{org_id}/data")
async def get_org_data(
    org_id: UUID4,
    member: schemas.AuthenticatedMember = Depends(get_current_active_member)
):
    return {"org_id": member.org_id, "role": member.role}
```

### Role-Based Permissions

#### Admin Only
```python
from ..auth import require_admin_role

@router.post("/{org_id}/invite-user")
async def invite_user(
    org_id: UUID4,
    admin_member: schemas.AuthenticatedMember = Depends(require_admin_role)
):
    # Only admins can invite users
    pass
```

#### Admin or Member (Blocks Viewers)
```python
from ..auth import require_admin_or_member_role

@router.post("/{org_id}/create-content")
async def create_content(
    org_id: UUID4,
    member: schemas.AuthenticatedMember = Depends(require_admin_or_member_role)
):
    # Admins and members can create content, viewers cannot
    pass
```

#### Any Active Member (Including Viewers)
```python
from ..auth import require_any_role

@router.get("/{org_id}/view-content")
async def view_content(
    org_id: UUID4,
    member: schemas.AuthenticatedMember = Depends(require_any_role)
):
    # All active members can view content
    pass
```

## Role Hierarchy

```
Admin (Level 3)    - Full access, can manage users
Member (Level 2)   - Can create content, cannot manage users  
Viewer (Level 1)   - Read-only access
```

## Helper Functions

### Role Permission Checks
```python
from ..auth import can_manage_users, can_create_content, can_view_content

# In your endpoint logic
if can_manage_users(member.role):
    # User can manage other users
    
if can_create_content(member.role):
    # User can create content
    
if can_view_content(member.role):
    # User can view content
```

### Role Hierarchy Comparison
```python
from ..auth import get_role_hierarchy_level, role_has_permission

# Check if user can manage another user
if role_has_permission(current_user_role, target_user_role):
    # Current user has permission to manage target user
```

### Custom Role Checks
```python
from ..auth import has_role_permission
from ..models import OrgRole

# Check if user has specific roles
if has_role_permission(member.role, [OrgRole.admin, OrgRole.member]):
    # User is admin or member
```

## Common Patterns

### 1. Dashboard/Default Organization
```python
@router.get("/dashboard")
async def get_dashboard(
    member: schemas.AuthenticatedMember = Depends(get_user_default_organization)
):
    return {
        "org_id": member.org_id,
        "role": member.role,
        "user": member.user.email
    }
```

### 2. Organization-Specific Resource
```python
@router.get("/{org_id}/projects")
async def get_projects(
    org_id: UUID4,
    member: schemas.AuthenticatedMember = Depends(require_any_role)
):
    # Get projects for this organization
    # member.org_id will always equal org_id (verified by auth)
    pass
```

### 3. Admin-Only Actions
```python
@router.delete("/{org_id}/users/{user_id}")
async def remove_user(
    org_id: UUID4,
    user_id: UUID4,
    admin_member: schemas.AuthenticatedMember = Depends(require_admin_role)
):
    # Only admins can remove users
    pass
```

### 4. Conditional Logic Based on Role
```python
@router.get("/{org_id}/data")
async def get_data(
    org_id: UUID4,
    member: schemas.AuthenticatedMember = Depends(require_any_role)
):
    data = {"basic": "data"}
    
    # Add admin-only data
    if member.role == OrgRole.admin:
        data["admin_secrets"] = "sensitive_data"
    
    # Add member+ data
    if can_create_content(member.role):
        data["creation_permissions"] = True
    
    return data
```

## Security Notes

### ✅ What's Protected
- **JWT Validation**: All tokens validated against Supabase
- **Database Checks**: All permissions verified in database
- **Role Verification**: Roles checked server-side
- **Organization Membership**: Active membership required

### ✅ Best Practices
- Always use auth dependencies instead of manual checks
- Use role-based dependencies for clear permission levels
- Check permissions at the endpoint level, not in business logic
- Use helper functions for complex permission logic

### ❌ What NOT to Do
- Don't trust client-side role information
- Don't skip auth dependencies
- Don't check permissions in frontend only
- Don't hardcode organization IDs

## Error Handling

The auth system provides clear error messages:

- `401 Unauthorized`: Invalid or missing JWT token
- `403 Forbidden`: User not a member of organization
- `403 Forbidden`: Insufficient role permissions
- `500 Internal Server Error`: Database or system errors

## Testing

Test different role scenarios:

```python
# Test with admin token
response = client.get("/orgs/123/admin-only-data", headers={"Authorization": f"Bearer {admin_token}"})
assert response.status_code == 200

# Test with viewer token (should fail)
response = client.get("/orgs/123/admin-only-data", headers={"Authorization": f"Bearer {viewer_token}"})
assert response.status_code == 403
```

## Migration from Old System

If you have existing endpoints, update them:

```python
# OLD WAY
@router.get("/{org_id}/data")
async def get_data(org_id: UUID4, user: schemas.SupabaseUser = Depends(get_current_user)):
    # Manual permission checking
    member = db.query(OrganizationMember).filter(...).first()
    if not member:
        raise HTTPException(403, "Not a member")
    # ... more manual checks

# NEW WAY  
@router.get("/{org_id}/data")
async def get_data(
    org_id: UUID4,
    member: schemas.AuthenticatedMember = Depends(require_any_role)
):
    # Permission already verified by dependency
    return {"data": "secure_data"}
```
