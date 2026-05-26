"""
Assessment Service — Pathneo
Port: 8001

Responsibilities (per HLD):
  - Career assessment engine (question delivery, scoring)
  - Assessment session management
  - Results storage and retrieval
  - Career cluster mapping

Run locally:
    uvicorn app.main:app --reload --port 8001
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Pathneo Assessment Service",
    description="Career assessment engine for the Pathneo platform.",
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
    return {"status": "healthy", "service": "assessment_service", "port": 8001}


# ── TODO: Register routers here as you build them ──────────────────────────────
# from app.api.v1.api import api_router
# app.include_router(api_router, prefix="/api/v1")
