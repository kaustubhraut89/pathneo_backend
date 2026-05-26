"""
Users router.

This file owns:
- HTTP routing and status codes
- OTP verification (before handing off to the service)
- Shared duplicate checks (email/phone) — these are role-agnostic
- db.commit() — one commit per request, at the outermost layer
- Response shaping

It does NOT own:
- Any DB model manipulation (delegated to app.services.signup)
- OTP generation/storage logic (app.core.otp)
- Schema definitions (app.schemas.signup)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import dependencies
from app.core.otp import otp_store
from app.core.security import generate_otp
from app.models.user import User
from app.schemas.signup import (
    SendOTPRequest,
    SignupRequest,
    ParentOnboarding,
    StudentSignup,
    SchoolSignup,
    CounsellorSignup,
)
from app.services.email import send_otp_email
from app.services import signup as signup_svc

router = APIRouter(prefix="/users", tags=["users"])


# ── OTP ───────────────────────────────────────────────────────────────────────

@router.post("/send-otp")
def send_otp(obj_in: SendOTPRequest, db: Session = Depends(dependencies.get_db)):
    """
    Send a one-time password to the given email address.
    Call this before any /signup endpoint.
    No DB write happens here.
    """
    existing = db.query(User).filter(User.email == obj_in.email).first()
    if existing and existing.verified:
        raise HTTPException(status_code=400, detail="Email already registered")

    code = generate_otp()
    otp_store.save(obj_in.email, code)
    send_otp_email(obj_in.email, code)

    return {
        "status": "success",
        "message": f"OTP sent to {obj_in.email}. Valid for 10 minutes.",
    }


# ── Shared pre-flight checks ──────────────────────────────────────────────────

def _verify_otp_or_raise(email: str, otp: str) -> None:
    if not otp_store.verify(email, otp):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")


def _check_no_duplicate_user(db: Session, *, email: str, phone: str) -> None:
    if db.query(User).filter(User.phone == phone).first():
        raise HTTPException(status_code=400, detail="Mobile number already registered")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")


# ── Unified signup ────────────────────────────────────────────────────────────

# Maps role literal → service function.
# To add a new role: add a schema with role: Literal["NEW_ROLE"] to SignupRequest
# and add an entry here. Nothing else changes.
_SIGNUP_HANDLERS = {
    "STUDENT":    signup_svc.signup_student,
    "SCHOOL":     signup_svc.signup_school,
    "COUNSELLOR": signup_svc.signup_counsellor,
}

@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(obj_in: SignupRequest, db: Session = Depends(dependencies.get_db)):
    """
    Unified signup endpoint. Discriminates by the `role` field.

    Supported roles: STUDENT | SCHOOL | COUNSELLOR

    Flow:
      POST /users/send-otp  →  POST /users/signup  →  POST /auth/login
    """
    _verify_otp_or_raise(obj_in.email, obj_in.otp)
    _check_no_duplicate_user(db, email=obj_in.email, phone=obj_in.mobile_number)

    result = _SIGNUP_HANDLERS[obj_in.role](db, obj_in)
    db.commit()

    return {"status": "success", "message": "Account created successfully.", **result}


# ── Parent onboarding (separate endpoint — two users, one OTP, different shape) ──

@router.post("/signup/parent", status_code=status.HTTP_201_CREATED)
def signup_parent(obj_in: ParentOnboarding, db: Session = Depends(dependencies.get_db)):
    """
    Parent + student onboarding in a single request.
    Only the parent's email receives an OTP. The student account is created
    immediately with a parent-set password.

    Flow:
      POST /users/send-otp (parent email)  →  POST /users/signup/parent  →  POST /auth/login
    """
    _verify_otp_or_raise(obj_in.parent.email, obj_in.parent.otp)

    # Duplicate checks are inside signup_svc.onboard_parent because they cover
    # two users (parent + student) — can't be handled by the shared helper above.
    result = signup_svc.onboard_parent(db, obj_in)
    db.commit()

    return {
        "status": "success",
        "message": "Onboarding successful. Student can now login with the set password.",
        **result,
    }