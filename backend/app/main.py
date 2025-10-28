from fastapi import FastAPI
from .routers import organizations
from .db import Base, engine
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="B2B SaaS MVP Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(organizations.router)

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

