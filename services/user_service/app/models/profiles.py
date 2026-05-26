from datetime import datetime, timezone, date
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text, Boolean, Date
from sqlalchemy.orm import relationship
from sqlalchemy.dialects import mysql
from app.db.session import Base

BIGINT = Integer().with_variant(mysql.BIGINT, "mysql")


class StudentProfile(Base):
    """
    Maps to the EXISTING 'student' table.
    Includes all fields from the signup schema.
    """
    __tablename__ = "student"

    student_id = Column(BIGINT, primary_key=True, autoincrement=True, index=True)
    user_id = Column(BIGINT, ForeignKey("users.id"), unique=True, nullable=True, index=True)

    # Profile Fields
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(255), nullable=True)
    city = Column(String(255), nullable=True)
    state = Column(String(255), nullable=True)
    country = Column(String(255), nullable=True)
    current_standard = Column(String(255), nullable=True)
    school_name = Column(String(255), nullable=True)
    college = Column(String(255), nullable=True)
    juniorcollege = Column(String(255), nullable=True)
    address = Column(String(3000), nullable=True)
    pincode = Column(String(255), nullable=True)
    contact = Column(BIGINT, nullable=True)
    preferred_language = Column(String(255), nullable=True, default="English")
    profile_image = Column(String(255), nullable=True)
    
    # Other legacy/extra fields
    active = Column(Boolean, default=True)
    career_interest = Column(String(255), nullable=True)
    hobbies = Column(String(255), nullable=True)
    skills = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User", foreign_keys=[user_id])


class ParentProfile(Base):
    """Maps to the 'parent_profiles' table."""
    __tablename__ = "parent_profiles"

    id = Column(BIGINT, primary_key=True, autoincrement=True, index=True)
    user_id = Column(BIGINT, ForeignKey("users.id"), unique=True, nullable=False, index=True)

    occupation = Column(String(255), nullable=True)
    city = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User", foreign_keys=[user_id])


class Counsellor(Base):
    """Maps to the EXISTING 'counsellor' table."""
    __tablename__ = "counsellor"

    counsellor_id = Column(BIGINT, primary_key=True, autoincrement=True, index=True)
    user_id = Column(BIGINT, ForeignKey("users.id"), unique=True, nullable=True, index=True)

    active = Column(Boolean, nullable=True)
    available_online = Column(Boolean, nullable=True)
    bio = Column(String(3000), nullable=True)
    consultation_fee = Column(mysql.DECIMAL(38, 2), nullable=True)
    experience_years = Column(Integer, nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    linkedin_url = Column(String(255), nullable=True)
    organization_name = Column(String(255), nullable=True)
    profile_image = Column(String(255), nullable=True)
    qualification = Column(String(255), nullable=True)
    specialization = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User", foreign_keys=[user_id])
