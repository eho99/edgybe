from fastapi import FastAPI
from fastapi.security import HTTPBearer
from .routers import organizations, users, members, student_guardian, invitations
from .db import Base, engine
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Edgybe")

# security = HTTPBearer()

# # Configure OpenAPI schema for Swagger UI authentication
# def custom_openapi():
#     if app.openapi_schema:
#         return app.openapi_schema
    
#     from fastapi.openapi.utils import get_openapi
#     openapi_schema = get_openapi(
#         title=app.title,
#         version="1.0.0",
#         description="Edgybe API",
#         routes=app.routes,
#     )
#     # Add Bearer token security scheme
#     openapi_schema["components"]["securitySchemes"] = {
#         "Bearer": {
#             "type": "http",
#             "scheme": "bearer",
#             "bearerFormat": "JWT",
#             "description": "Enter your Supabase JWT token (without 'Bearer ' prefix)"
#         }
#     }
#     app.openapi_schema = openapi_schema
#     return app.openapi_schema

# app.openapi = custom_openapi

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(organizations.router)
app.include_router(users.router)
app.include_router(members.router)
app.include_router(student_guardian.router)
app.include_router(invitations.router)

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

