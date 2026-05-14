import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Tuple
import config
from models.schemas import GeneratedEmail


def send_email(email: GeneratedEmail) -> Tuple[bool, str]:
    """
    Send (or mock-send) an email based on EMAIL_MODE in config.
    Returns (success: bool, message: str).
    """
    mode = config.EMAIL_MODE.lower()

    if mode == "dry_run":
        return _dry_run(email)
    elif mode == "smtp":
        return _send_smtp(email)
    elif mode == "sendgrid":
        return _send_sendgrid(email)
    else:
        return False, f"Unknown EMAIL_MODE '{mode}'"


# ── Dry Run ─────────────────────────────────────────────────────────────────────

def _dry_run(email: GeneratedEmail) -> Tuple[bool, str]:
    print(f"\n{'='*60}")
    print(f"[DRY RUN] Would send email to: {email.client_email}")
    print(f"  Subject : {email.subject}")
    print(f"  Stage   : {email.stage.value}  |  Tone: {email.tone}")
    print(f"  Invoice : {email.invoice_no}  |  Amount: {email.currency} {email.amount:,.2f}")
    print(f"{'='*60}\n")
    return True, "dry_run"


# ── SMTP ────────────────────────────────────────────────────────────────────────

def _send_smtp(email: GeneratedEmail) -> Tuple[bool, str]:
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = email.subject
        msg["From"] = f"{config.FROM_NAME} <{config.FROM_EMAIL}>"
        msg["To"] = email.client_email

        # Plain text version
        text_part = MIMEText(email.body, "plain")
        # HTML version (wrap body in simple HTML)
        html_body = email.body.replace("\n", "<br>")
        html_part = MIMEText(
            f"<html><body style='font-family:Arial,sans-serif;line-height:1.6'>{html_body}</body></html>",
            "html",
        )
        msg.attach(text_part)
        msg.attach(html_part)

        context = ssl.create_default_context()
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
            server.ehlo()
            server.starttls(context=context)
            server.login(config.SMTP_USER, config.SMTP_PASSWORD)
            server.sendmail(config.FROM_EMAIL, email.client_email, msg.as_string())

        return True, "sent_smtp"
    except Exception as exc:
        return False, f"smtp_error: {exc}"


# ── SendGrid ────────────────────────────────────────────────────────────────────

def _send_sendgrid(email: GeneratedEmail) -> Tuple[bool, str]:
    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail, Email, To, Content

        sg = sendgrid.SendGridAPIClient(api_key=config.SENDGRID_API_KEY)
        message = Mail(
            from_email=Email(config.FROM_EMAIL, config.FROM_NAME),
            to_emails=To(email.client_email),
            subject=email.subject,
            plain_text_content=Content("text/plain", email.body),
        )
        response = sg.client.mail.send.post(request_body=message.get())
        if response.status_code in (200, 202):
            return True, "sent_sendgrid"
        return False, f"sendgrid_status_{response.status_code}"
    except ImportError:
        return False, "sendgrid package not installed (pip install sendgrid)"
    except Exception as exc:
        return False, f"sendgrid_error: {exc}"
