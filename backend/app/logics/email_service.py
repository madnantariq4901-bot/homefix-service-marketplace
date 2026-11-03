import smtplib
import ssl
from email.message import EmailMessage

from app.config import settings


def ensure_email_configured() -> None:
    if not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL:
        raise RuntimeError("Password reset email is not configured; set SMTP_HOST and SMTP_FROM_EMAIL")


def send_password_reset_email(email: str, reset_url: str) -> None:
    ensure_email_configured()

    message = EmailMessage()
    message["Subject"] = "Reset your password"
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = email
    message.set_content(
        "We received a request to reset the password for your account.\n\n"
        f"Use this link within {settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutes:\n"
        f"{reset_url}\n\n"
        "If you did not request this, you can ignore this email."
    )

    context = ssl.create_default_context()
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
        if settings.SMTP_USE_TLS:
            server.starttls(context=context)
        if settings.SMTP_USERNAME:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(message)
