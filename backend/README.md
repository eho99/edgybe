# Backend Setup Guide

## Quick Start

1. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your Supabase credentials
   ```

4. **Run database migrations**:
   ```bash
   alembic revision --autogenerate -m "Initial schema"
   alembic upgrade head
   ```

5. **Start the development server**:
   ```bash
   uvicorn app.main:app --reload
   ```

## Environment Variables

Create a `.env` file with the following variables:

```env
# Supabase project URL and keys
SUPABASE_URL="https://your-project-id.supabase.co"
SUPABASE_SERVICE_KEY="your-supabase-service-role-key"

# Direct Postgres connection string for Alembic & SQLAlchemy
# Get this from Supabase: Settings > Database > Connection string > URI
DATABASE_URL="postgresql://postgres:[YOUR-PASSWORD]@db.your-project-id.supabase.co:5432/postgres"

# JWT Secret (fallback validation, though we prefer .get_user())
# Get this from Supabase: Settings > API > JWT Settings
SUPABASE_JWT_SECRET="your-supabase-jwt-secret"
```

## Database Migrations

This project uses Alembic for database migrations. Never modify the database schema directly.

### Creating Migrations
```bash
# Generate migration from model changes
alembic revision --autogenerate -m "Description of changes"

# Apply migration
alembic upgrade head
```

### Migration Commands
```bash
# Show current revision
alembic current

# Show migration history
alembic history

# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>
```

## API Development

### Adding New Endpoints

1. **Create Pydantic schemas** in `app/schemas.py`
2. **Add SQLAlchemy models** in `app/models.py` (if needed)
3. **Create migration** for model changes
4. **Add router endpoints** in `app/routers/`
5. **Use auth dependencies**:
   - `get_current_user()` for basic authentication
   - `get_current_active_member()` for org-specific access

### Authentication Dependencies

```python
from ..auth import get_current_user, get_current_active_member

# Basic authentication
@router.get("/protected")
async def protected_endpoint(
    user: schemas.SupabaseUser = Depends(get_current_user)
):
    return {"user_id": user.id}

# Organization-specific access
@router.get("/orgs/{org_id}/data")
async def org_endpoint(
    org_id: UUID4,
    member: schemas.AuthenticatedMember = Depends(get_current_active_member)
):
    return {"org_id": member.org_id, "role": member.role}
```

## Testing the API

### Health Check
```bash
curl http://localhost:8000/api/health
```

### Protected Endpoint (requires JWT)
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:8000/api/v1/organizations/ORG_ID/protected-data
```

## Troubleshooting

### Common Issues

1. **Database connection errors**: Check your `DATABASE_URL` in `.env`
2. **JWT validation errors**: Verify `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`
3. **Migration errors**: Ensure all model imports are in `alembic/env.py`

### Debug Mode
```bash
# Run with debug logging
uvicorn app.main:app --reload --log-level debug
```

