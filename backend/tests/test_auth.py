def test_signup_creates_customer(client):
    resp = client.post(
        "/auth/signup",
        json={
            "email": "alice@example.com",
            "password": "password123",
            "full_name": "Alice",
            "role": "customer",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "alice@example.com"
    assert body["role"] == "customer"
    assert "hashed_password" not in body  # never leak the hash
 
 
def test_signup_provider_also_creates_provider_profile(client):
    resp = client.post(
        "/auth/signup",
        json={
            "email": "bob@example.com",
            "password": "password123",
            "full_name": "Bob",
            "role": "provider",
        },
    )
    assert resp.status_code == 201
 
    login = client.post("/auth/login", json={"email": "bob@example.com", "password": "password123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
 
    me = client.get("/providers/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["is_verified"] is False
    assert me.json()["is_available"] is False
 
 
def test_signup_duplicate_email_fails(client, customer):
    _, user = customer
    resp = client.post(
        "/auth/signup",
        json={
            "email": user["email"],
            "password": "password123",
            "full_name": "Someone Else",
            "role": "customer",
        },
    )
    assert resp.status_code == 400
 
 
def test_signup_rejects_short_password(client):
    resp = client.post(
        "/auth/signup",
        json={
            "email": "short@example.com",
            "password": "short",
            "full_name": "Short Pass",
            "role": "customer",
        },
    )
    assert resp.status_code == 422
 
 
def test_login_success_returns_bearer_token(client, customer):
    _, user = customer
    resp = client.post("/auth/login", json={"email": user["email"], "password": "password123"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
 
 
def test_login_wrong_password_fails(client, customer):
    _, user = customer
    resp = client.post("/auth/login", json={"email": user["email"], "password": "wrong-password"})
    assert resp.status_code == 401
 
 
def test_login_nonexistent_user_fails(client):
    resp = client.post("/auth/login", json={"email": "nobody@example.com", "password": "password123"})
    assert resp.status_code == 401


def test_forgot_password_sends_reset_link_without_disclosing_account(client, customer, db_session, monkeypatch):
    import hashlib

    from app.config import settings
    from app.database.models.password_reset_token import PasswordResetToken
    import app.logics.auth_service as auth_service

    _, user = customer
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "no-reply@example.com")
    reset_links = []
    monkeypatch.setattr(
        auth_service,
        "send_password_reset_email",
        lambda email, reset_url: reset_links.append((email, reset_url)),
    )

    response = client.post("/auth/forgot-password", json={"email": user["email"]})
    unknown_response = client.post("/auth/forgot-password", json={"email": "nobody@example.com"})

    assert response.status_code == 200
    assert response.json() == unknown_response.json()
    assert len(reset_links) == 1
    assert reset_links[0][0] == user["email"]
    assert "/auth/reset-password?token=" in reset_links[0][1]
    raw_token = reset_links[0][1].split("token=", 1)[1]
    reset_token = db_session.query(PasswordResetToken).one()
    assert reset_token.token_hash == hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def test_reset_password_changes_password_and_token_is_single_use(client, customer, monkeypatch):
    from app.config import settings
    import app.logics.auth_service as auth_service

    _, user = customer
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "no-reply@example.com")
    reset_link = []
    monkeypatch.setattr(auth_service, "send_password_reset_email", lambda email, url: reset_link.append(url))

    requested = client.post("/auth/forgot-password", json={"email": user["email"]})
    token = reset_link[0].split("token=", 1)[1]
    reset = client.post(
        "/auth/reset-password",
        json={"token": token, "new_password": "new-password-123"},
    )
    reused = client.post(
        "/auth/reset-password",
        json={"token": token, "new_password": "another-password-123"},
    )

    assert requested.status_code == 200
    assert reset.status_code == 200
    assert reused.status_code == 400
    assert client.post(
        "/auth/login",
        json={"email": user["email"], "password": "new-password-123"},
    ).status_code == 200
    assert client.post(
        "/auth/login",
        json={"email": user["email"], "password": "password123"},
    ).status_code == 401


def test_reset_password_rejects_invalid_expired_and_short_passwords(client, customer, db_session, monkeypatch):
    from datetime import datetime, timedelta, timezone

    from app.config import settings
    from app.database.models.password_reset_token import PasswordResetToken
    import app.logics.auth_service as auth_service

    _, user = customer
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "no-reply@example.com")
    reset_link = []
    monkeypatch.setattr(auth_service, "send_password_reset_email", lambda email, url: reset_link.append(url))
    client.post("/auth/forgot-password", json={"email": user["email"]})
    token = reset_link[0].split("token=", 1)[1]
    reset_record = db_session.query(PasswordResetToken).one()
    reset_record.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db_session.commit()

    invalid = client.post(
        "/auth/reset-password",
        json={"token": "not-a-valid-token", "new_password": "new-password-123"},
    )
    expired = client.post(
        "/auth/reset-password",
        json={"token": token, "new_password": "new-password-123"},
    )
    short = client.post(
        "/auth/reset-password",
        json={"token": "not-a-valid-token", "new_password": "short"},
    )

    assert invalid.status_code == 400
    assert expired.status_code == 400
    assert short.status_code == 422


def test_seeded_maryam_demo_account_can_log_in(client, db_session):
    from seed import seed

    seed(db_session)

    response = client.post(
        "/auth/login",
        json={"email": "cleaner@example.com", "password": "DemoProvider123"},
    )

    assert response.status_code == 200
    profile = client.get(
        "/providers/me",
        headers={"Authorization": f"Bearer {response.json()['access_token']}"},
    )
    assert profile.status_code == 200
    assert profile.json()["is_verified"] is True
    opportunities = client.get(
        "/jobs/available",
        headers={"Authorization": f"Bearer {response.json()['access_token']}"},
    )
    assert opportunities.status_code == 200
    assert any("deep clean" in job["description"].lower() for job in opportunities.json())


def test_seed_migrates_legacy_demo_provider_email(client, db_session):
    from app.core.security import hash_password
    from app.models import ProviderProfile, User, UserRole
    from seed import seed

    legacy_user = User(
        email="cleaner@demo.local",
        hashed_password=hash_password("DemoProvider123"),
        full_name="Maryam Hassan",
        role=UserRole.PROVIDER,
    )
    db_session.add(legacy_user)
    db_session.commit()
    db_session.refresh(legacy_user)
    profile = ProviderProfile(user_id=legacy_user.id, is_verified=True, is_available=True)
    db_session.add(profile)
    db_session.commit()
    original_user_id = legacy_user.id
    original_profile_id = profile.id

    seed(db_session)

    migrated = db_session.query(User).filter(User.email == "cleaner@example.com").one()
    assert migrated.id == original_user_id
    assert db_session.query(User).filter(User.email == "cleaner@demo.local").count() == 0
    assert db_session.query(ProviderProfile).filter(ProviderProfile.id == original_profile_id).count() == 1
    response = client.post(
        "/auth/login",
        json={"email": "cleaner@example.com", "password": "DemoProvider123"},
    )
    assert response.status_code == 200


def test_protected_route_without_token_fails(client):
    resp = client.get("/providers/me")
    assert resp.status_code == 401
 
 
def test_protected_route_with_garbage_token_fails(client):
    resp = client.get("/providers/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401
 