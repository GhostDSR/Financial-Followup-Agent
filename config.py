import os
from dotenv import load_dotenv

load_dotenv()

# ── LLM ────────────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
LLM_MODEL: str = os.getenv("LLM_MODEL", "claude-sonnet-4-20250514")
LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "1024"))

# ── Email ───────────────────────────────────────────────────────────────────────
EMAIL_MODE: str = os.getenv("EMAIL_MODE", "dry_run")   # "dry_run" | "smtp" | "sendgrid"
SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER: str = os.getenv("SMTP_USER", "")
SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY", "")
FROM_EMAIL: str = os.getenv("FROM_EMAIL", "finance@yourcompany.com")
FROM_NAME: str = os.getenv("FROM_NAME", "Finance Team")

# ── Data ────────────────────────────────────────────────────────────────────────
DATA_FILE: str = os.getenv("DATA_FILE", "data/sample_invoices.csv")

# ── Audit ───────────────────────────────────────────────────────────────────────
AUDIT_DB: str = os.getenv("AUDIT_DB", "logs/audit.db")
AUDIT_JSON: str = os.getenv("AUDIT_JSON", "logs/audit_log.json")

# ── Company ─────────────────────────────────────────────────────────────────────
COMPANY_NAME: str = os.getenv("COMPANY_NAME", "Acme Corp")
COMPANY_PHONE: str = os.getenv("COMPANY_PHONE", "+91-11-2345-6789")
COMPANY_EMAIL: str = os.getenv("COMPANY_EMAIL", "finance@yourcompany.com")


def validate_config() -> list[str]:
    """Return a list of missing / misconfigured settings."""
    issues = []
    if not ANTHROPIC_API_KEY:
        issues.append("ANTHROPIC_API_KEY is not set")
    if EMAIL_MODE == "smtp" and not SMTP_USER:
        issues.append("SMTP_USER is required when EMAIL_MODE=smtp")
    if EMAIL_MODE == "sendgrid" and not SENDGRID_API_KEY:
        issues.append("SENDGRID_API_KEY is required when EMAIL_MODE=sendgrid")
    return issues
