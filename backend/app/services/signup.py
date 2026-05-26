from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.security import get_password_hash
from app.models.user import User, Role, School, UserTenantRole
from app.models.profiles import Counsellor          # ← import your Counsellor model
from app.models.links import ParentStudentLink
from app.services.profiles import create_role_profile
from app.schemas.signup import (
    StudentSignup,
    SchoolSignup,
    CounsellorSignup,
    ParentOnboarding,
    StudentCreate,
)

_SYSTEM_INDEPENDENT_PHONE = "SYSTEM_INDEPENDENT"


# ── Internal helpers ──────────────────────────────────────────────────────────

def _make_user(db: Session, *, first_name: str, last_name: str, email: str,
               phone: str, password: str, role: str,
               status: str = "active", verified: bool = True) -> User:
    user = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        password=get_password_hash(password),
        role=role,
        status=status,
        verified=verified,
    )
    db.add(user)
    db.flush()
    return user


def _get_or_create_role(db: Session, name: str) -> Role:
    role = db.query(Role).filter(Role.name == name).first()
    if not role:
        role = Role(name=name)
        db.add(role)
        db.flush()
    return role


def _assign_role(db: Session, *, user_id: int, school_id: int, role_name: str) -> None:
    role = _get_or_create_role(db, role_name)
    db.add(UserTenantRole(user_id=user_id, school_id=school_id, role_id=role.id))


def _get_or_create_independent_school(db: Session) -> School:
    school = db.query(School).filter(School.school_name == "Independent").first()
    if school:
        return school

    sys_admin = db.query(User).filter(User.phone == _SYSTEM_INDEPENDENT_PHONE).first()
    if not sys_admin:
        sys_admin = User(
            first_name="System",
            last_name="Independent",
            email="independent@pathneo.com",
            phone=_SYSTEM_INDEPENDENT_PHONE,
            password="SYSTEM_LOCKED",
            role="ADMIN",
            status="active",
        )
        db.add(sys_admin)
        db.flush()

    school = School(school_name="Independent", user_id=sys_admin.id, active=True)
    db.add(school)
    db.flush()
    return school


# ── Public signup functions ───────────────────────────────────────────────────

def signup_student(db: Session, data: StudentSignup) -> dict:
    school_id = data.school_id
    if not school_id:
        school_id = _get_or_create_independent_school(db).school_id

    user = _make_user(
        db,
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        phone=data.mobile_number,
        password=data.password,
        role="STUDENT",
    )
    _assign_role(db, user_id=user.id, school_id=school_id, role_name="STUDENT")

    _EXCLUDE = {"role", "otp", "password", "email", "mobile_number",
                "first_name", "last_name", "school_id"}
    create_role_profile(
        db, user.id, "STUDENT", school_id,
        first_name=data.first_name,
        last_name=data.last_name,
        **data.model_dump(exclude=_EXCLUDE),
    )

    return {"user_id": user.id}


def signup_school(db: Session, data: SchoolSignup) -> dict:
    if db.query(School).filter(School.school_name == data.school_name).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="School name already registered",
        )

    admin = _make_user(
        db,
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        phone=data.mobile_number,
        password=data.password,
        role="SCHOOL",
    )

    school = School(
        school_name=data.school_name,
        user_id=admin.id,
        active=True,
        address=data.school_address,
        city=data.school_city,
        state=data.school_state,
        pincode=data.school_pincode,
        principal_name=data.school_principal,
        board=data.school_board,
        website=data.school_website,
        description=data.school_description,
        established_year=data.school_established_year,
        logo=data.school_logo,
        school_type=data.school_type,
        total_students=data.school_total_students,
    )
    db.add(school)
    db.flush()

    _assign_role(db, user_id=admin.id, school_id=school.school_id, role_name="SCHOOL")

    return {"user_id": admin.id, "school_id": school.school_id}


def signup_counsellor(db: Session, data: CounsellorSignup) -> dict:
    user = _make_user(
        db,
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        phone=data.mobile_number,
        password=data.password,
        role="COUNSELLOR",
    )

    # Create counsellor profile record
    counsellor = Counsellor(
        user_id=user.id,
        first_name=data.first_name,
        last_name=data.last_name,
        bio=data.bio,
        qualification=data.qualification,
        specialization=data.specialization,
        experience_years=data.experience_years,
        consultation_fee=data.consultation_fee,
        organization_name=data.organization_name,
        linkedin_url=data.linkedin_url,
        profile_image=data.profile_image,
        available_online=data.available_online,
        active=data.active,
    )
    db.add(counsellor)
    db.flush()

    # Optionally link to a school tenant
    if data.school_id:
        school = db.query(School).filter(School.school_id == data.school_id).first()
        if not school:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="School not found")
        _assign_role(db, user_id=user.id, school_id=data.school_id,
                     role_name="COUNSELLOR")

    return {"user_id": user.id, "counsellor_id": counsellor.counsellor_id}


def _create_student_for_parent(db: Session, data: StudentCreate, school_id: int) -> User:
    student = _make_user(
        db,
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        phone=data.mobile_number,
        password=data.password,
        role="STUDENT",
    )
    _assign_role(db, user_id=student.id, school_id=school_id, role_name="STUDENT")

    _EXCLUDE = {"password", "email", "mobile_number", "first_name",
                "last_name", "school_id"}
    create_role_profile(
        db, student.id, "STUDENT", school_id,
        first_name=data.first_name,
        last_name=data.last_name,
        **data.model_dump(exclude=_EXCLUDE),
    )
    return student


def onboard_parent(db: Session, data: ParentOnboarding) -> dict:
    p = data.parent
    s = data.student

    if db.query(User).filter(User.phone == p.mobile_number).first():
        raise HTTPException(status_code=400, detail="Parent mobile number already registered")
    if db.query(User).filter(User.email == p.email).first():
        raise HTTPException(status_code=400, detail="Parent email already registered")
    if db.query(User).filter(User.phone == s.mobile_number).first():
        raise HTTPException(status_code=400, detail="Student mobile number already registered")
    if db.query(User).filter(User.email == s.email).first():
        raise HTTPException(status_code=400, detail="Student email already registered")

    school_id = s.school_id
    if not school_id:
        school_id = _get_or_create_independent_school(db).school_id

    parent = _make_user(
        db,
        first_name=p.first_name,
        last_name=p.last_name,
        email=p.email,
        phone=p.mobile_number,
        password=p.password,
        role="PARENT",
    )
    _assign_role(db, user_id=parent.id, school_id=school_id, role_name="PARENT")

    student = _create_student_for_parent(db, s, school_id)

    db.add(ParentStudentLink(
        parent_id=parent.id,
        student_id=student.id,
        relationship_type=data.relationship_type,
        is_verified=True,
    ))

    return {"parent_id": parent.id, "student_id": student.id}