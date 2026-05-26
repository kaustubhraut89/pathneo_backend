from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.api.dependencies import get_db
from app.core.security import get_password_hash
from app.core.config import settings
from app.models.user import User, Role, School, UserTenantRole

router = APIRouter(prefix="/internal", tags=["internal"])


# ─── Master Secret Guard ──────────────────────────────────────────────────────
MASTER_SECRET = "PATHNEOMASTERKEY2026"  # Move to settings.MASTER_SECRET in prod

def verify_master_secret(x_master_secret: str = Header(...)):
    if x_master_secret != MASTER_SECRET:
        raise HTTPException(status_code=403, detail="Invalid master secret")


# ─── Schema ───────────────────────────────────────────────────────────────────
class InternalUserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    mobile_number: str
    password: str
    role: str  # ADMIN or GOVERNMENT


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/signup/admin", dependencies=[Depends(verify_master_secret)])
def create_admin(
    obj_in: InternalUserCreate,
    db: Session = Depends(get_db)
):
    """
    Create an ADMIN account.
    Requires X-Master-Secret header.
    Only accessible server-side — never expose to frontend.
    """
    if obj_in.role != "ADMIN":
        raise HTTPException(status_code=400, detail="This endpoint is for ADMIN role only")

    if db.query(User).filter(User.email == obj_in.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    if db.query(User).filter(User.phone == obj_in.mobile_number).first():
        raise HTTPException(status_code=400, detail="Phone already registered")

    user = User(
        first_name=obj_in.first_name,
        last_name=obj_in.last_name,
        email=obj_in.email,
        phone=obj_in.mobile_number,
        password=get_password_hash(obj_in.password),
        role="ADMIN",
        status="active",
        verified=True
    )
    db.add(user)
    db.flush()

    role_obj = db.query(Role).filter(Role.name == "ADMIN").first()
    if not role_obj:
        role_obj = Role(name="ADMIN")
        db.add(role_obj)
        db.flush()

    school = db.query(School).filter(School.school_name == "Independent").first()
    if school:
        db.add(UserTenantRole(
            user_id=user.id,
            school_id=school.school_id,
            role_id=role_obj.id
        ))

    db.commit()
    return {
        "status": "success",
        "user_id": user.id,
        "role": "ADMIN",
        "message": "Admin account created successfully"
    }


@router.post("/signup/government", dependencies=[Depends(verify_master_secret)])
def create_government(
    obj_in: InternalUserCreate,
    db: Session = Depends(get_db)
):
    """
    Create a GOVERNMENT account.
    Requires X-Master-Secret header.
    Only accessible server-side — never expose to frontend.
    """
    if obj_in.role != "GOVERNMENT":
        raise HTTPException(status_code=400, detail="This endpoint is for GOVERNMENT role only")

    if db.query(User).filter(User.email == obj_in.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    if db.query(User).filter(User.phone == obj_in.mobile_number).first():
        raise HTTPException(status_code=400, detail="Phone already registered")

    user = User(
        first_name=obj_in.first_name,
        last_name=obj_in.last_name,
        email=obj_in.email,
        phone=obj_in.mobile_number,
        password=get_password_hash(obj_in.password),
        role="GOVERNMENT",
        status="active",
        verified=True
    )
    db.add(user)
    db.flush()

    role_obj = db.query(Role).filter(Role.name == "GOVERNMENT").first()
    if not role_obj:
        role_obj = Role(name="GOVERNMENT")
        db.add(role_obj)
        db.flush()

    school = db.query(School).filter(School.school_name == "Independent").first()
    if school:
        db.add(UserTenantRole(
            user_id=user.id,
            school_id=school.school_id,
            role_id=role_obj.id
        ))

    db.commit()
    return {
        "status": "success",
        "user_id": user.id,
        "role": "GOVERNMENT",
        "message": "Government account created successfully"
    }