from datetime import date
from decimal import Decimal
from typing import Annotated, Literal, Optional, Union
from pydantic import BaseModel, EmailStr, Field


# ── Shared base ───────────────────────────────────────────────────────────────

class _SignupBase(BaseModel):
    first_name: str
    last_name: str
    mobile_number: str
    email: EmailStr
    otp: str
    password: str


# ── Role-specific schemas ─────────────────────────────────────────────────────

class StudentSignup(_SignupBase):
    role: Literal["STUDENT"]
    school_id: Optional[int] = None
    date_of_birth: date
    gender: str
    city: str
    state: str
    country: str
    current_standard: str
    school_name: Optional[str] = None
    college: Optional[str] = None
    address: Optional[str] = None
    pincode: Optional[str] = None
    contact: Optional[str] = None
    preferred_language: Optional[str] = "English"
    profile_image: Optional[str] = None


class SchoolSignup(_SignupBase):
    role: Literal["SCHOOL"]
    # Required
    school_name: str
    # Optional — all map directly to School table columns
    school_address: Optional[str] = None
    school_city: Optional[str] = None
    school_state: Optional[str] = None
    school_pincode: Optional[str] = None
    school_principal: Optional[str] = None
    school_board: Optional[str] = None
    school_website: Optional[str] = None
    school_description: Optional[str] = None
    school_established_year: Optional[int] = None
    school_logo: Optional[str] = None
    school_type: Optional[str] = None
    school_total_students: Optional[int] = None


class CounsellorSignup(_SignupBase):
    role: Literal["COUNSELLOR"]
    # Optional school link
    school_id: Optional[int] = None
    # Counsellor profile fields — all optional at signup
    bio: Optional[str] = None
    qualification: Optional[str] = None
    specialization: Optional[str] = None
    experience_years: Optional[int] = None
    consultation_fee: Optional[Decimal] = None
    organization_name: Optional[str] = None
    linkedin_url: Optional[str] = None
    profile_image: Optional[str] = None
    available_online: Optional[bool] = False
    active: Optional[bool] = True


# ── Parent onboarding ─────────────────────────────────────────────────────────

class _ParentBase(BaseModel):
    first_name: str
    last_name: str
    mobile_number: str
    email: EmailStr
    otp: str
    password: str


class StudentCreate(BaseModel):
    first_name: str
    last_name: str
    mobile_number: str
    email: EmailStr
    password: str
    date_of_birth: date
    gender: str
    city: str
    state: str
    country: str
    current_standard: str
    school_id: Optional[int] = None
    school_name: Optional[str] = None
    college: Optional[str] = None
    address: Optional[str] = None
    pincode: Optional[str] = None
    contact: Optional[str] = None
    preferred_language: Optional[str] = "English"
    profile_image: Optional[str] = None


class ParentOnboarding(BaseModel):
    parent: _ParentBase
    student: StudentCreate
    relationship_type: str


# ── Discriminated union for unified /signup ───────────────────────────────────

SignupRequest = Annotated[
    Union[StudentSignup, SchoolSignup, CounsellorSignup],
    Field(discriminator="role"),
]


# ── Misc ──────────────────────────────────────────────────────────────────────

class SendOTPRequest(BaseModel):
    email: EmailStr