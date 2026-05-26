"""
AI Service — Pathneo
Port: 8003

Responsibilities (per HLD):
  - AI-powered career roadmap generation (Anthropic / OpenAI)
  - Personalised career path recommendations
  - LLM prompt management
  - Response caching (Redis)

Run locally:
    uvicorn app.main:app --reload --port 8003
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Pathneo AI Service",
    description="LLM-powered career roadmap and recommendation engine for the Pathneo platform.",
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
    return {"status": "healthy", "service": "ai_service", "port": 8003}


# ── TODO: Register routers here as you build them ──────────────────────────────
# from app.api.v1.api import api_router
# app.include_router(api_router, prefix="/api/v1")
