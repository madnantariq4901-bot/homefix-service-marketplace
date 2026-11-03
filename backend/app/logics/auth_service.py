import hashlib
import logging
import secrets
import smtplib
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status # pyright: ignore[reportMissingImports]
from sqlalchemy.exc import IntegrityError, SQLAlchemyError # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import Session # pyright: ignore[reportMissingImports]

from app.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.database.models.password_reset_token import PasswordResetToken
from app.database.models.provider import ProviderProfile
from app.database.models.user import User, UserRole
from app.logics.email_service import ensure_email_configured, send_password_reset_email
from app.schemas.user import UserCreate

logger = logging.getLogger(__name__)


def signup_user(db: Session, payload: UserCreate) -> User:
    email = str(payload.email).lower()
    if payload.role == UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator accounts cannot be registered here")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = User(
        email=email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name.strip(),
        phone=payload.phone.strip() if payload.phone else None,
        role=payload.role,
    )
    try:
        db.add(user)
        db.flush()
        if user.role == UserRole.PROVIDER:
            db.add(ProviderProfile(user_id=user.id))
        db.commit()
        db.refresh(user)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered") from exc
    return user


def authenticate_user(db: Session, email: str, password: str) -> str:
    user = db.query(User).filter(User.email == email.lower()).first()
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return create_access_token(user_id=user.id, role=user.role.value)


def request_password_reset(db: Session, email: str) -> None:
    try:
        ensure_email_configured()
    except RuntimeError as exc:
        logger.error("%s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Password reset email is temporarily unavailable",
        ) from exc

    user = db.query(User).filter(User.email == email.lower()).first()
    if user is None:
        return

    raw_token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at.is_(None),
    ).update({PasswordResetToken.used_at: now}, synchronize_session=False)
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=hashlib.sha256(raw_token.encode("utf-8")).hexdigest(),
            expires_at=now + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES),
        )
    )

    reset_url = f"{settings.FRONTEND_BASE_URL}/auth/reset-password?token={raw_token}"
    try:
        send_password_reset_email(user.email, reset_url)
    except (OSError, RuntimeError, smtplib.SMTPException) as exc:
        db.rollback()
        logger.exception("Could not send password reset email")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Password reset email is temporarily unavailable",
        ) from exc
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise


def reset_password(db: Session, token: str, new_password: str) -> None:
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_hash,
        PasswordResetToken.used_at.is_(None),
    ).first()
    if reset_token is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset link")

    expires_at = reset_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset link")

    user = db.query(User).filter(User.id == reset_token.user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset link")

    now = datetime.now(timezone.utc)
    consumed = db.query(PasswordResetToken).filter(
        PasswordResetToken.id == reset_token.id,
        PasswordResetToken.used_at.is_(None),
    ).update({PasswordResetToken.used_at: now}, synchronize_session=False)
    if consumed != 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset link")

    user.hashed_password = hash_password(new_password)
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.id != reset_token.id,
        PasswordResetToken.used_at.is_(None),
    ).update({PasswordResetToken.used_at: now}, synchronize_session=False)
    db.commit()
