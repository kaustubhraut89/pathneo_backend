"""
School Service — Pathneo
Port: 8004

Responsibilities (per HLD):
  - School/institution management (CRUD)
  - Counsellor–student assignment
  - School-scoped RBAC tenant configuration
  - School analytics and reporting

Run locally:
    uvicorn app.main:app --reload --port 8004
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Pathneo School Service",
    description="School and institution management for the Pathneo platform.",
    version="0.1.0",
    openapi_url="/api/v1/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    return {"status": "healthy", "service": "school_service", "port": 8004}


# ── TODO: Register routers here as you build them ──────────────────────────────
# from app.api.v1.api import api_router
# app.include_router(api_router, prefix="/api/v1")
