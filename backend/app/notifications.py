import os
import smtplib
from email.message import EmailMessage
import logging

LOGGER = logging.getLogger(__name__)

SMTP_HOST = os.environ.get('SMTP_HOST')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USER = os.environ.get('SMTP_USER')
SMTP_PASS = os.environ.get('SMTP_PASS')
SMTP_FROM = os.environ.get('SMTP_FROM', SMTP_USER or 'noreply@example.com')


def send_email(to_email: str, subject: str, body: str) -> bool:
    """Send an email using configured SMTP. Returns True on success."""
    if not SMTP_HOST or not SMTP_USER or not SMTP_PASS:
        LOGGER.info("SMTP not configured; skipping email to %s", to_email)
        return False
    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = SMTP_FROM
        msg['To'] = to_email
        msg.set_content(body)
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
        LOGGER.info("Sent notification email to %s", to_email)
        return True
    except Exception as e:
        LOGGER.exception("Failed to send email: %s", e)
        return False
