# B2B SaaS MVP

A multi-tenant B2B SaaS application built with FastAPI backend, Next.js frontend, and Supabase Auth. This project demonstrates a clean, extensible, and production-ready architecture for B2B applications.

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Next.js       │    │   Supabase      │    │   FastAPI       │
│   Frontend      │◄──►│   Auth          │    │   Backend       │
│                 │    │                 │    │                 │
│ • Login/Logout  │    │ • JWT Tokens    │    │ • Business Logic│
│ • Dashboard     │    │ • User Mgmt     │    │ • Org Mgmt      │
│ • API Calls     │    │ • Password Reset│    │ • JWT Validation│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────────────────────────────┐
                       │         Supabase Postgres              │
                       │                                         │
                       │ • auth.users (Supabase managed)        │
                       │ • organizations (custom tables)        │
                       │ • profiles (links to auth.users)       │
                       │ • organization_members (junction)      │
                       └─────────────────────────────────────────┘
```

### Key Architecture Decisions

1. **Frontend → Supabase Auth**: Direct communication for login, logout, password reset
2. **Frontend → FastAPI**: All business logic with JWT authentication
3. **FastAPI → Supabase**: JWT validation and admin operations
4. **Database**: Single Supabase Postgres instance with Alembic migrations

## Project Structure

```
./
├── backend/                    # FastAPI backend
│   ├── alembic/               # Database migrations
│   ├── app/                   # Application code
│   │   ├── routers/           # API endpoints
│   │   ├── auth.py            # JWT validation & dependencies
│   │   ├── db.py              # Database connection
│   │   ├── models.py          # SQLAlchemy models
│   │   ├── schemas.py         # Pydantic schemas
│   │   └── main.py            # FastAPI app
│   ├── requirements.txt       # Python dependencies
│   └── .env.example           # Environment variables
│
└── frontend/                  # Next.js frontend
    ├── app/                   # App Router structure
    │   ├── (app)/             # Protected routes
    │   ├── (auth)/            # Public auth routes
    │   └── globals.css        # Global styles
    ├── lib/                   # Utilities
    │   ├── supabaseClient.ts  # Supabase client
    │   └── apiClient.ts       # FastAPI client wrapper
    ├── components/            # React components
    └── .env.local.example     # Environment variables
```

## Security Model

### Authentication Flow
1. User logs in via Supabase Auth (frontend)
2. Supabase returns JWT token
3. Frontend stores token and sends it to FastAPI
4. FastAPI validates token with Supabase
5. FastAPI checks user's organization membership
6. Access granted/denied based on membership status

### Authorization Levels
- **Superadmin**: Can create organizations (not implemented in this MVP)
- **Org Admin**: Can invite users, manage roles within their org
- **Org Member**: Can access org data based on their role
- **Org Viewer**: Read-only access to org data

## Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js 18+
- Supabase account and project

### Backend Setup

1. **Create virtual environment**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your Supabase credentials
   ```

4. **Run database migrations**:
   ```bash
   alembic revision --autogenerate -m "Initial schema"
   alembic upgrade head
   ```

5. **Start the server**:
   ```bash
   uvicorn app.main:app --reload
   ```

### Frontend Setup

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Configure environment**:
   ```bash
   cp .env.local.example .env.local
   # Edit .env.local with your Supabase credentials
   ```

3. **Start the development server**:
   ```bash
   npm run dev
   ```

## Development Workflow

### Adding New API Endpoints

1. **Create Pydantic schemas** in `backend/app/schemas.py`
2. **Add SQLAlchemy models** in `backend/app/models.py` (if needed)
3. **Create migration**:
   ```bash
   alembic revision --autogenerate -m "Description of changes"
   alembic upgrade head
   ```
4. **Add router endpoints** in `backend/app/routers/`
5. **Use auth dependencies**:
   - `get_current_user()` for basic authentication
   - `get_current_active_member()` for org-specific access

### Adding New Frontend Pages

1. **Protected routes**: Add to `app/(app)/` directory
2. **Public routes**: Add to `app/(auth)/` directory
3. **Use `apiClient`** for all FastAPI calls
4. **Auth guard** is automatically applied to `(app)` routes

### Database Migrations

Always use Alembic for schema changes:

```bash
# Create new migration
alembic revision --autogenerate -m "Add new table"

# Review the generated migration file
# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

## API Endpoints

### Organizations
- `GET /api/v1/organizations/{org_id}/protected-data` - Example protected endpoint

### Health Check
- `GET /api/health` - Service health status

## Environment Variables

### Backend (.env)
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_SERVICE_KEY`: Service role key for admin operations
- `DATABASE_URL`: Direct Postgres connection string
- `SUPABASE_JWT_SECRET`: JWT secret for token validation

### Frontend (.env.local)
- `NEXT_PUBLIC_SUPABASE_URL`: Public Supabase URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`: Public anon key
- `NEXT_PUBLIC_API_BASE_URL`: FastAPI backend URL

## Key Features Implemented

✅ **Authentication**: Supabase Auth integration  
✅ **Authorization**: Organization-based access control  
✅ **Database**: Alembic migrations with foreign key to auth.users  
✅ **Type Safety**: Strict TypeScript with proper error handling  
✅ **Security**: JWT validation on every request  
✅ **UI**: Modern design with Tailwind CSS and shadcn/ui  
✅ **Architecture**: Clean separation of concerns  

## Next Steps

- [ ] Implement superadmin functionality
- [ ] Add user invitation system
- [ ] Add role management within organizations
- [ ] Implement user profile management
- [ ] Add more comprehensive error handling
- [ ] Add API documentation with FastAPI's automatic docs
- [ ] Add unit tests for backend
- [ ] Add integration tests for frontend

## Contributing

1. Follow the existing code structure
2. Use Alembic for all database changes
3. Maintain type safety in TypeScript
4. Test authentication flows thoroughly
5. Update documentation for new features

