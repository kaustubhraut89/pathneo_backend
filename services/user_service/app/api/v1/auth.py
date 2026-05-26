from datetime import timedelta, datetime, timezone
from typing import Optional
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from jose import jwt, JWTError

from app.api.dependencies import get_db, PermissionChecker
from app.core.security import verify_password, create_access_token, get_password_hash
from app.core.config import settings
from app.models.user import User, UserTenantRole

router = APIRouter(prefix="/auth", tags=["auth"])

# ─── Internal roles — excluded from forgot password ───────────────────────────
INTERNAL_ROLES = ("ADMIN", "GOVERNMENT")

# ─── Frontend reset URL — change this when frontend is deployed ───────────────
RESET_PASSWORD_URL = "http://localhost:3000/reset-password"

ALGORITHM = "HS256"


# ─── Schemas ──────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    identifier: str
    password: str
    school_id: Optional[int] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    role: Optional[str]
    school_id: Optional[int]

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    confirm_password: str


# ─── Reset Token Helpers ──────────────────────────────────────────────────────

def _generate_reset_token(user_id: int, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    payload = {
        "sub": str(user_id),
        "email": email,
        "purpose": "password_reset",
        "exp": expire
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def _verify_reset_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("purpose") != "password_reset":
            return None
        return payload
    except JWTError:
        return None


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
            detail=f"Too many login attempts. Try again in {WINDOW_MINUTES} minutes or reset your password using 'Forgot Password'"
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


def _send_reset_email(email: str, first_name: str, reset_link: str):
    """Send password reset email with button."""
    from app.services.email import send_email
    subject = "Reset your Pathneo password"
    html_content = f"""
    <html><body style="margin:0;padding:0;background:#f0f4f8;font-family:Arial,sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="padding:40px 0;">
        <tr><td align="center">
          <table width="520" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:16px;overflow:hidden;border:1px solid #e0e0e0;">
            <tr>
              <td style="background:#1a1a2e;padding:28px 32px;text-align:center;">
                <span style="font-size:28px;font-weight:700;color:#ffffff;letter-spacing:-1px;">Path</span><span style="font-size:28px;font-weight:300;color:#00D4FF;letter-spacing:-1px;">neo</span>
              </td>
            </tr>
            <tr>
              <td style="padding:40px 32px 24px;text-align:center;">
                <h2 style="margin:0 0 12px;font-size:24px;font-weight:700;color:#1a1a2e;">Reset Password Request</h2>
                <p style="margin:0 0 8px;font-size:15px;color:#374151;">Hello <strong>{first_name}</strong>,</p>
                <p style="margin:0;font-size:15px;color:#6b7280;line-height:1.7;">
                  To reset your Pathneo account password, click the button below.
                </p>
              </td>
            </tr>
            <tr>
              <td style="padding:8px 32px 32px;text-align:center;">
                <a href="{reset_link}" style="display:inline-block;background:#1a1a2e;color:#ffffff;text-decoration:none;font-size:16px;font-weight:bold;padding:16px 48px;border-radius:8px;">
                  Reset Password
                </a>
              </td>
            </tr>
            <tr>
              <td style="padding:0 32px 32px;text-align:center;">
                <p style="margin:0;font-size:13px;color:#9ca3af;">
                  Note: This link is valid for <strong>24 hours</strong>.
                </p>
                <p style="margin:12px 0 0;font-size:12px;color:#9ca3af;">
                  If you did not request a password reset, you can safely ignore this email.
                </p>
              </td>
            </tr>
            <tr>
              <td style="padding:16px 32px;border-top:1px solid #e0e0e0;text-align:center;">
                <p style="margin:0;font-size:12px;color:#9ca3af;">© 2026 Pathneo. All rights reserved.</p>
              </td>
            </tr>
          </table>
        </td></tr>
      </table>
    </body></html>
    """
    send_email(email_to=email, subject=subject, html_content=html_content)


# ─── Login ────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
def login(
    request: Request,
    obj_in: LoginRequest,
    db: Session = Depends(get_db)
):
    """Universal login for all user types."""
    ip = request.client.host
    _check_rate_limit(ip)

    user = db.query(User).filter(
        (User.phone == obj_in.identifier) | (User.email == obj_in.identifier)
    ).first()

    if not user:
        _record_attempt(ip)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect phone/email or password")

    if not verify_password(obj_in.password, user.password):
        _record_attempt(ip)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect phone/email or password")

    if not user.verified:
        _record_attempt(ip)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified. Please complete signup verification.")

    if user.status != "active":
        _record_attempt(ip)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive. Please contact support.")

    _clear_attempts(ip)

    school_id = obj_in.school_id
    role_name = user.role

    if school_id:
        user_school_role = db.query(UserTenantRole).filter(
            UserTenantRole.user_id == user.id,
            UserTenantRole.school_id == school_id,
        ).first()
        if not user_school_role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not belong to the specified school.")
        role_name = user_school_role.role.name
    else:
        first_membership = db.query(UserTenantRole).filter(
            UserTenantRole.user_id == user.id
        ).first()
        if first_membership:
            school_id = first_membership.school_id
            role_name = first_membership.role.name

    permissions = _get_user_permissions(db, user.id, school_id) if school_id else []

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


# ─── Forgot Password ──────────────────────────────────────────────────────────

@router.post("/forgot-password")
def forgot_password(
    obj_in: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Send password reset link to email.
    Not available for ADMIN and GOVERNMENT roles.
    """
    user = db.query(User).filter(User.email == obj_in.email).first()

    if not user or user.role in INTERNAL_ROLES:
        raise HTTPException(
            status_code=404,
            detail="No account exists for this email id. Please recheck the email id."
        )

    if user.status != "active":
        raise HTTPException(status_code=400, detail="Account is inactive. Please contact support.")

    # Generate reset token
    reset_token = _generate_reset_token(user.id, user.email)
    reset_link = f"{RESET_PASSWORD_URL}?token={reset_token}"

    # Send email in background
    background_tasks.add_task(
        _send_reset_email,
        user.email,
        user.first_name,
        reset_link
    )

    return {
        "status": "success",
        "message": f"We have sent an email to {obj_in.email} with instructions for password reset. Please check your spam/junk folder in case you don't receive it in your inbox."
    }


# ─── Reset Password ───────────────────────────────────────────────────────────

@router.post("/reset-password")
def reset_password(
    obj_in: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Verify reset token and set new password.
    Frontend sends token from URL + new password + confirm password.
    """
    # 1. Validate passwords match
    if obj_in.new_password != obj_in.confirm_password:
        raise HTTPException(status_code=400, detail="The passwords don't match. Please recheck.")

    if len(obj_in.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    # 2. Verify token
    payload = _verify_reset_token(obj_in.token)
    if not payload:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link. Please request a new one.")

    # 3. Find user
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 4. Block internal roles
    if user.role in INTERNAL_ROLES:
        raise HTTPException(status_code=403, detail="Password reset not allowed for this account type")

    # 5. Update password
    user.password = get_password_hash(obj_in.new_password)
    db.commit()

    return {
        "status": "success",
        "message": "Password reset successfully. You can now login with your new password."
    }


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