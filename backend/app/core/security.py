from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"

def create_access_token(
    subject: Union[str, Any], 
    tenant_id: int = None,
    permissions: list[str] = None,
    expires_delta: timedelta = None
) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {
        "exp": expire, 
        "sub": str(subject),
        "sid": tenant_id,
        "perms": permissions or []
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

import hashlib

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Pre-hash with SHA-256 to support passwords > 72 chars
    sha256_password = hashlib.sha256(plain_password.encode()).hexdigest()
    return pwd_context.verify(sha256_password, hashed_password)

def get_password_hash(password: str) -> str:
    # Pre-hash with SHA-256 to support passwords > 72 chars
    sha256_password = hashlib.sha256(password.encode()).hexdigest()
    return pwd_context.hash(sha256_password)

def generate_onboarding_token(user_id: int) -> str:
    """Generate a token for student activation/onboarding (valid for 24h)"""
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    to_encode = {
        "exp": expire,
        "sub": str(user_id),
        "purpose": "onboarding"
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)

def verify_onboarding_token(token: str) -> Optional[int]:
    """Verify onboarding token and return user_id"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("purpose") != "onboarding":
            return None
        return int(payload.get("sub"))
    except (jwt.JWTError, ValueError):
        return None

import random
import string

import secrets

def generate_otp(length: int = 6) -> str:
    first = secrets.choice(string.digits[1:])  # 1-9
    rest = "".join(secrets.choice(string.digits) for _ in range(length - 1))
    return first + rest
