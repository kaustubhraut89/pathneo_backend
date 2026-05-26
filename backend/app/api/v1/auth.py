from datetime import timedelta, datetime, timezone
from typing import Optional
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.dependencies import get_db, PermissionChecker
from app.core.security import verify_password, create_access_token
from app.core.config import settings
from app.models.user import User, UserTenantRole

router = APIRouter(prefix="/auth", tags=["auth"])


# ─── Schemas ─────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    """Single login for ALL user types: student, parent, school, counsellor, admin."""
    identifier: str
    password: str
    school_id: Optional[int] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    role: Optional[str]
    school_id: Optional[int]


# ─── Rate Limiter ─────────────────────────────────────────────────────────────

_login_attempts: dict = defaultdict(list)
MAX_ATTEMPTS = 5
WINDOW_MINUTES = 10


def _check_rate_limit(ip: str):
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=WINDOW_MINUTES)
    _login_attempts[ip] = [t for t in _login_attempts[ip] if t > window_start]
    if len(_login_attempts[ip]) >= MAX_ATTEMPTS:
        raise HTTPException(
            status_code=429,
            detail=f"Too many login attempts. Try again in {WINDOW_MINUTES} minutes."
        )


def _record_attempt(ip: str):
    _login_attempts[ip].append(datetime.now(timezone.utc))


def _clear_attempts(ip: str):
    _login_attempts.pop(ip, None)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _get_user_permissions(db: Session, user_id: int, school_id: int) -> list[str]:
    user_school_role = db.query(UserTenantRole).filter(
        UserTenantRole.user_id == user_id,
        UserTenantRole.school_id == school_id,
    ).first()
    if not user_school_role:
        return []
    role = user_school_role.role
    return [perm.code for perm in role.permissions]


# ─── Login ────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
def login(
    request: Request,
    obj_in: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Universal login for all user types (student, parent, school, counsellor, admin).
    Accepts phone or email + password.
    Returns a JWT with user_id, role, school_id, and permissions.
    """
    ip = request.client.host

    # 0. Rate limit check
    _check_rate_limit(ip)

    # 1. Find user
    user = db.query(User).filter(
        (User.phone == obj_in.identifier) | (User.email == obj_in.identifier)
    ).first()

    if not user:
        _record_attempt(ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect phone/email or password"
        )

    # 2. Verify password
    if not verify_password(obj_in.password, user.password):
        _record_attempt(ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect phone/email or password"
        )

    # 3. Check email verification
    if not user.verified:
        _record_attempt(ip)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please complete signup verification."
        )

    # 4. Check account status
    if user.status != "active":
        _record_attempt(ip)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact support."
        )

    # 5. Success — clear attempts
    _clear_attempts(ip)

    # 6. Resolve school context
    school_id = obj_in.school_id
    role_name = user.role

    if school_id:
        user_school_role = db.query(UserTenantRole).filter(
            UserTenantRole.user_id == user.id,
            UserTenantRole.school_id == school_id,
        ).first()
        if not user_school_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not belong to the specified school."
            )
        role_name = user_school_role.role.name
    else:
        first_membership = db.query(UserTenantRole).filter(
            UserTenantRole.user_id == user.id
        ).first()
        if first_membership:
            school_id = first_membership.school_id
            role_name = first_membership.role.name

    # 7. Permissions
    permissions = _get_user_permissions(db, user.id, school_id) if school_id else []

    # 8. Create JWT
    access_token = create_access_token(
        subject=str(user.id),
        tenant_id=school_id,
        permissions=permissions,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return TokenResponse(
        access_token=access_token,
        user_id=user.id,
        role=role_name,
        school_id=school_id,
    )


# ─── Me ───────────────────────────────────────────────────────────────────────

@router.get("/me")
def get_me(
    current_user: User = Depends(PermissionChecker([]))
):
    """Return current user profile from JWT context."""
    return {
        "id": current_user.id,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "email": current_user.email,
        "phone": current_user.phone,
        "role": current_user.role,
        "status": current_user.status,
        "verified": current_user.verified,
        "current_school_id": current_user.current_school_id,
        "current_permissions": current_user.current_permissions,
    }