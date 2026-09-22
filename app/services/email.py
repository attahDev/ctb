import smtplib
from email.message import EmailMessage

from app.core.config import settings


def send_email(to: str, subject: str, body: str) -> None:
    """Best-effort email send. Silently no-ops if SMTP isn't configured,
    so local dev and early deploys don't crash on missing credentials."""
    if not settings.smtp_host:
        print(f"[email skipped - no SMTP configured] to={to} subject={subject}")
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from
    msg["To"] = to
    msg.set_content(body)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
    except Exception as exc:  # noqa: BLE001
        print(f"[email send failed] to={to} error={exc}")
