"""Shared test fixtures and test database setup."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.models.admin import AdminAccount, AccessLevel
from app.core.security import hash_password


# Use SQLite for tests
TEST_DATABASE_URL = "sqlite:///./test_prismid.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def disable_rate_limit():
    """Disable rate limiting for tests."""
    if hasattr(app.state, "limiter"):
        app.state.limiter.enabled = False
    yield
    if hasattr(app.state, "limiter"):
        app.state.limiter.enabled = True


@pytest.fixture(autouse=True)
def setup_db():
    """Create tables before each test, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    """Provide a test database session."""
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    """Provide a test HTTP client."""
    return TestClient(app)


@pytest.fixture
def superadmin(db):
    """Create and return a superadmin account."""
    admin = AdminAccount(
        username="testadmin",
        password_hash=hash_password("TestPass123"),
        email="admin@test.com",
        access_level=AccessLevel.SUPERADMIN,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


@pytest.fixture
def viewer(db):
    """Create and return a viewer account."""
    account = AdminAccount(
        username="testviewer",
        password_hash=hash_password("ViewerPass123"),
        email="viewer@test.com",
        access_level=AccessLevel.VIEWER,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@pytest.fixture
def superadmin_token(client, superadmin):
    """Get JWT token for superadmin."""
    response = client.post("/api/auth/login", json={
        "username": "testadmin",
        "password": "TestPass123",
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture
def viewer_token(client, viewer):
    """Get JWT token for viewer."""
    response = client.post("/api/auth/login", json={
        "username": "testviewer",
        "password": "ViewerPass123",
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


def auth_header(token):
    """Helper to build authorization header."""
    return {"Authorization": f"Bearer {token}"}
