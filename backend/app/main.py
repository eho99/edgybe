from fastapi import FastAPI
from fastapi.security import HTTPBearer
from .routers import organizations, users, members, student_guardian, invitations, referrals
from .db import Base, engine
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

app = FastAPI(title="Edgybe")
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000", 
        "https://adminreferral.com",
        "https://www.adminreferral.com",
        "https://edgybe.vercel.app",
        ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(organizations.router)
app.include_router(users.router)
app.include_router(users.public_router)
app.include_router(members.router)
app.include_router(student_guardian.router)
app.include_router(invitations.router)
app.include_router(referrals.router)

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

