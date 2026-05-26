from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.dialects import mysql
from app.db.session import Base

# Compatibility: Use Integer for SQLite (supports autoincrement), but BIGINT for MySQL
BIGINT = Integer().with_variant(mysql.BIGINT, "mysql")

# Junction Table for Roles and Permissions
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id"), primary_key=True),
)

class School(Base):
    """Represents a School or Organization (Maps to existing 'school' table)"""
    __tablename__ = "school"
    school_id = Column(BIGINT, primary_key=True, autoincrement=True, index=True)
    school_name = Column(String(255), nullable=False)
    active = Column(Boolean, default=True)
    address = Column(String(1000), nullable=True)
    board = Column(String(255), nullable=True)
    city = Column(String(255), nullable=True)
    state = Column(String(255), nullable=True)
    pincode = Column(String(255), nullable=True)
    principal_name = Column(String(255), nullable=True)
    school_type = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    description = Column(String(3000), nullable=True)
    established_year = Column(Integer, nullable=True)
    logo = Column(String(255), nullable=True)
    total_students = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    user_id = Column(BIGINT, ForeignKey("users.id"), nullable=True)  # Admin of school

class Permission(Base):
    """Action-based permissions (e.g., 'assessment:read')"""
    __tablename__ = "permissions"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    code = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(String(255))

class Role(Base):
    """User roles (e.g., 'STUDENT', 'SCHOOL_ADMIN')"""
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    
    permissions = relationship("Permission", secondary=role_permissions, backref="roles")

class UserTenantRole(Base):
    """Links Users to Schools with specific Roles (Multi-tenancy)"""
    __tablename__ = "user_school_roles"
    user_id = Column(BIGINT, ForeignKey("users.id"), primary_key=True)
    school_id = Column(BIGINT, ForeignKey("school.school_id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id"), primary_key=True)
    
    user = relationship("User", back_populates="school_roles")
    school = relationship("School")
    role = relationship("Role")

class User(Base):
    """Maps to existing 'users' table"""
    __tablename__ = "users"

    id = Column(BIGINT, primary_key=True, autoincrement=True, index=True)
    first_name = Column(String(255))
    last_name = Column(String(255))
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(255), unique=True, index=True)
    password = Column(String(255), nullable=False) # Hashed
    role = Column(mysql.ENUM('ADMIN','COUNSELLOR','GOVERNMENT','PARENT','SCHOOL','STUDENT'), nullable=False)
    status = Column(String(255), nullable=False, default="active")
    otp = Column(String(255), nullable=True)
    otp_expiry = Column(DateTime, nullable=True)
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    school_roles = relationship("UserTenantRole", back_populates="user")
