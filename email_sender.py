"""
SMTP email sender for Project Sentinel.
Sends HTML confirmation emails after capital call approval.
"""
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def validate_email(email: str) -> bool:
    """Basic email format validation."""
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def send_confirmation_email(
    smtp_server: str, smtp_port: int, smtp_user: str, smtp_password: str,
    to_email: str, subject: str, html_body: str, from_email: str = None
) -> tuple[bool, str]:
    """Send an HTML email. Returns (success, message)."""
    try:
        if not validate_email(to_email):
            return False, f"Invalid recipient email format: {to_email}"

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_email or smtp_user
        msg["To"] = to_email

        # Plain text fallback
        plain_text = html_body.replace("<br>", "\n").replace("&nbsp;", " ")
        plain_text = re.sub(r"<[^>]+>", "", plain_text)

        msg.attach(MIMEText(plain_text, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, to_email, msg.as_string())

        return True, f"Email sent to {to_email}"
    except smtplib.SMTPAuthenticationError:
        return False, "SMTP authentication failed. Check your email and password."
    except smtplib.SMTPConnectError:
        return False, f"Could not connect to SMTP server {smtp_server}:{smtp_port}."
    except TimeoutError:
        return False, "Connection timed out. Check SMTP server and port settings."
    except Exception as e:
        return False, f"Failed to send: {str(e)}"
