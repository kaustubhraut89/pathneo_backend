from datetime import datetime, timezone
from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects import mysql
from app.db.session import Base

BIGINT = Integer().with_variant(mysql.BIGINT, "mysql")

class ParentStudentLink(Base):
    """Relationship between a Parent and a Student"""
    __tablename__ = "parent_student_links"
    
    parent_id = Column(BIGINT, ForeignKey("users.id"), primary_key=True)
    student_id = Column(BIGINT, ForeignKey("users.id"), primary_key=True)
    relationship_type = Column(String(50))  # e.g., "mother", "father", "guardian"
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    parent = relationship("User", foreign_keys=[parent_id])
    student = relationship("User", foreign_keys=[student_id])

class CounsellorStudentLink(Base):
    """Relationship between a Counsellor and a Student"""
    __tablename__ = "counsellor_student_links"
    
    counsellor_id = Column(BIGINT, ForeignKey("users.id"), primary_key=True)
    student_id = Column(BIGINT, ForeignKey("users.id"), primary_key=True)
    assigned_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    counsellor = relationship("User", foreign_keys=[counsellor_id])
    student = relationship("User", foreign_keys=[student_id])
