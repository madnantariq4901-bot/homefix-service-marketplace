import os
import subprocess
import sys


def test_security_headers_and_auth_responses_are_not_cached(client, customer):
    response = client.get("/categories")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert response.headers["permissions-policy"] == "camera=(), microphone=(), geolocation=(self)"

    headers, user = customer
    login = client.post("/auth/login", json={"email": user["email"], "password": "password123"})
    assert login.status_code == 200
    assert login.headers["cache-control"] == "no-store"
    assert login.headers["pragma"] == "no-cache"


def test_production_rejects_placeholder_database_credentials():
    environment = os.environ.copy()
    environment.update(
        {
            "ENVIRONMENT": "production",
            "JWT_SECRET": "a" * 40,
            "DATABASE_URL": "postgresql+psycopg2://marketplace_user:change-this-password@db.example/app",
        }
    )
    result = subprocess.run(
        [sys.executable, "-c", "import app.config"],
        cwd=os.path.dirname(os.path.dirname(__file__)),
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "explicit DATABASE_URL credentials" in result.stderr