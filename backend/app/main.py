from fastapi import FastAPI
from .routers import organizations, users, members, student_guardian, invitations
from .db import Base, engine
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Edgybe")

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

