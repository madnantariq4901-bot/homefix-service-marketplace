import os
from pathlib import Path

from dotenv import load_dotenv # pyright: ignore[reportMissingImports]

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

DEFAULT_DATABASE_URL = "postgresql+psycopg2://marketplace_user:change-this-password@localhost:5432/service_marketplace"
DEFAULT_JWT_SECRET = "local-development-secret-change-before-deployment"


class Settings:
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development").strip().lower()
    DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    JWT_SECRET = os.getenv("JWT_SECRET", DEFAULT_JWT_SECRET)
    JWT_ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES = int(os.getenv("PASSWORD_RESET_TOKEN_EXPIRE_MINUTES", "60"))
    SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "").strip()
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "").strip()
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").strip().lower() in {"1", "true", "yes"}
    FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000").rstrip("/")
    CALLOUT_FEE = float(os.getenv("CALLOUT_FEE", "10.00"))
    IDENTITY_UPLOAD_DIR = Path(
        os.getenv("IDENTITY_UPLOAD_DIR", str(Path(__file__).resolve().parents[1] / "private_uploads"))
    )
    FRONTEND_ORIGINS = [
        origin.strip()
        for origin in os.getenv(
            "FRONTEND_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001",
        ).split(",")
        if origin.strip()
    ]


settings = Settings()

if settings.ENVIRONMENT == "development":
    for local_origin in ("http://localhost:3001", "http://127.0.0.1:3001"):
        if local_origin not in settings.FRONTEND_ORIGINS:
            settings.FRONTEND_ORIGINS.append(local_origin)

if settings.ENVIRONMENT == "production" and (
    settings.JWT_SECRET == DEFAULT_JWT_SECRET
    or len(settings.JWT_SECRET) < 32
    or settings.DATABASE_URL == DEFAULT_DATABASE_URL
    or "change-this-password" in settings.DATABASE_URL
):
    raise RuntimeError("Production requires a private JWT_SECRET and explicit DATABASE_URL credentials")
