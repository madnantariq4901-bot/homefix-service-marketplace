import pytest # pyright: ignore[reportMissingImports]
from sqlalchemy import create_engine # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import sessionmaker # pyright: ignore[reportMissingImports]
from sqlalchemy.pool import StaticPool # pyright: ignore[reportMissingImports]
from fastapi.testclient import TestClient # pyright: ignore[reportMissingImports]
 
from app.main import app
from app.database import Base, get_db
from app.models import ServiceCategory, CategoryName
 
# Shared in-memory SQLite DB for the whole test run; StaticPool keeps the
# same connection alive across threads (TestClient runs in a worker thread).
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
 
 
def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
 
 
app.dependency_overrides[get_db] = _override_get_db
 
 
@pytest.fixture(autouse=True)
def _fresh_db(tmp_path, monkeypatch):
    """Create all tables before each test, drop them after -> full isolation."""
    from app.config import settings

    monkeypatch.setattr(settings, "IDENTITY_UPLOAD_DIR", tmp_path / "identity")
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
 
 
@pytest.fixture()
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
 
 
@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c
 
 
@pytest.fixture()
def make_user(client):
    """Sign up a user via the real API and return (headers, user_json)."""
 
    def _make_user(email="user@example.com", password="password123", full_name="Test User", role="customer", phone=None):
        resp = client.post(
            "/auth/signup",
            json={
                "email": email,
                "password": password,
                "full_name": full_name,
                "phone": phone,
                "role": role,
            },
        )
        assert resp.status_code == 201, resp.text
        user = resp.json()
 
        login = client.post("/auth/login", json={"email": email, "password": password})
        assert login.status_code == 200, login.text
        token = login.json()["access_token"]
 
        return {"Authorization": f"Bearer {token}"}, user
 
    return _make_user
 
 
@pytest.fixture()
def customer(make_user):
    return make_user(email="customer@example.com", role="customer")
 
 
@pytest.fixture()
def provider(make_user):
    return make_user(email="provider@example.com", role="provider")
 
 
@pytest.fixture()
def category(db_session):
    """Insert a service category directly (bypasses the admin-only endpoint)."""
    cat = ServiceCategory(name=CategoryName.PLUMBER, base_hourly_rate=25.0, description="Plumbing work")
    db_session.add(cat)
    db_session.commit()
    db_session.refresh(cat)
    return cat
 