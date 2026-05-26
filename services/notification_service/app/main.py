"""
Notification Service — Pathneo
Port: 8002

Responsibilities (per HLD):
  - Email notifications (OTP, alerts, reports)
  - SMS notifications via MSG91
  - Push notifications (future)
  - Notification templates and history

Run locally:
    uvicorn app.main:app --reload --port 8002
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Pathneo Notification Service",
    description="Email, SMS, and push notification delivery for the Pathneo platform.",
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
    return {"status": "healthy", "service": "notification_service", "port": 8002}


# ── TODO: Register routers here as you build them ──────────────────────────────
# from app.api.v1.api import api_router
# app.include_router(api_router, prefix="/api/v1")
