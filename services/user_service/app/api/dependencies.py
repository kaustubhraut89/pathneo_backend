from typing import Generator, List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from pydantic import BaseModel, ValidationError

from app.db.session import SessionLocal
from app.core.config import settings
from app.core.security import ALGORITHM
from app.models.user import User

security = HTTPBearer()

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    sid: Optional[int] = None # School ID
    perms: List[str] = []

def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

def get_current_user(
    db: Session = Depends(get_db), 
    auth: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    token = auth.credentials
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = db.query(User).filter(User.id == token_data.sub).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.status != "active":
        raise HTTPException(status_code=400, detail="Inactive user")

    # Inject runtime context from token
    user.current_school_id = token_data.sid
    user.current_permissions = token_data.perms
    
    return user

class PermissionChecker:
    """Action-based permission checker dependency"""
    def __init__(self, required_permissions: List[str]):
        self.required_permissions = required_permissions

    def __call__(self, user: User = Depends(get_current_user)):
        # Check if all required permissions are in the user's current token perms
        for perm in self.required_permissions:
            if perm not in user.current_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permission: {perm}",
                )
        return user
