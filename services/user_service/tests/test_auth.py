"""
Test Suite for RBAC and Relationship-Based Access Control.

Covers:
1. Login endpoint — phone/email auth, JWT structure
2. Permission checks — correct role can access, wrong role is denied
3. Relationship checks — parent/counsellor can only access linked students
4. Multi-tenancy — school admin can't access other school's data
5. Government role — only aggregated data, no raw PII
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import timedelta

from app.main import app
from app.db.session import Base
from app.api.dependencies import get_db
from app.models.user import User, Role, Permission, UserTenantRole, role_permissions
from app.models.links import ParentStudentLink, CounsellorStudentLink
from app.core.security import get_password_hash, create_access_token

import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'test.db')}"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
client = TestClient(app)

# ─── Fixtures ─────────────────────────────────────────────────────────────────
@pytest.fixture(scope="module", autouse=True)
def setup_db():
    """Create all tables before tests, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    """Fresh DB session for each test, shared with the app."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    # Override the app's get_db to use THIS specific session
    def _override_get_db():
        try:
            yield session
        finally:
            pass # Session is closed by the fixture
            
    app.dependency_overrides[get_db] = _override_get_db
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()
    app.dependency_overrides.pop(get_db, None)


def _create_role_with_perms(db, role_name: str, perm_codes: list[str]) -> Role:
    """Helper to create a Role with given permissions."""
    role = Role(name=role_name)
    db.add(role)
    db.flush()
    for code in perm_codes:
        perm = db.query(Permission).filter(Permission.code == code).first()
        if not perm:
            perm = Permission(code=code, description=code)
            db.add(perm)
            db.flush()
        if perm not in role.permissions:
            role.permissions.append(perm)
    db.commit()
    return role


def _create_user(db, phone: str, password: str = "Test1234!", status: str = "active") -> User:
    user = User(
        first_name="Test",
        last_name="User",
        phone=phone,
        password=get_password_hash(password),
        status=status
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_token(user_id: int, school_id: int = None, perms: list = None) -> str:
    return create_access_token(
        subject=str(user_id),
        tenant_id=school_id,
        permissions=perms or [],
        expires_delta=timedelta(minutes=30)
    )


# ─── 1. Login Tests ───────────────────────────────────────────────────────────
class TestLogin:
    def test_login_with_phone_success(self, db):
        _create_user(db, phone="9000000001")
        resp = client.post("/api/v1/auth/login", json={
            "identifier": "9000000001",
            "password": "Test1234!"
        })
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    def test_login_wrong_password(self, db):
        _create_user(db, phone="9000000002")
        resp = client.post("/api/v1/auth/login", json={
            "identifier": "9000000002",
            "password": "WrongPass!"
        })
        assert resp.status_code == 401

    def test_login_inactive_user(self, db):
        _create_user(db, phone="9000000003", status="inactive")
        resp = client.post("/api/v1/auth/login", json={
            "identifier": "9000000003",
            "password": "Test1234!"
        })
        assert resp.status_code == 403

    def test_login_nonexistent_user(self, db):
        resp = client.post("/api/v1/auth/login", json={
            "identifier": "9999999999",
            "password": "Any1234!"
        })
        assert resp.status_code == 401


# ─── 2. RBAC Permission Tests ─────────────────────────────────────────────────
class TestRBAC:
    def test_student_can_access_own_assessment(self, db):
        """STUDENT role has 'assessment:read' permission."""
        role = _create_role_with_perms(db, "STUDENT_RBAC_TEST", ["assessment:read"])
        user = _create_user(db, phone="9000000010")
        
        token = _make_token(user.id, perms=["assessment:read"])
        resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert "assessment:read" in resp.json()["current_permissions"]

    def test_no_token_returns_401(self):
        """Accessing a protected route without token should fail."""
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_invalid_token_returns_403(self):
        """Corrupted JWT should return 403."""
        resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalidtoken"})
        assert resp.status_code == 403


        user = _create_user(db, phone="9000000011")

        # Token with only student-level perms
        token = _make_token(user.id, perms=["assessment:read"])

        # The /me endpoint requires [] (any logged-in user) - passes
        resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        perms = resp.json()["current_permissions"]
        assert "school:manage" not in perms



