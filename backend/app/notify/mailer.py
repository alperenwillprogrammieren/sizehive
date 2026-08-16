"""Outbound mail.

Without `smtp_host` configured, mail is logged instead of sent. That's the
default in dev, and it is deliberately not a silent no-op: the login link
and every notification body land in the application log, so the whole flow
stays exercisable without an SMTP server.
"""
import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_mail(to: str, subject: str, body: str) -> None:
    if not settings.smtp_host:
        logger.info(
            "SMTP not configured — mail not sent. To: %s | Subject: %s\n%s",
            to,
            subject,
            body,
        )
        return

    message = EmailMessage()
    message["From"] = settings.mail_from
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        if settings.smtp_starttls:
            smtp.starttls()
        if settings.smtp_user:
            smtp.login(settings.smtp_user, settings.smtp_password or "")
        smtp.send_message(message)

    logger.info("sent mail to %s: %s", to, subject)
