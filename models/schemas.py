from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from enum import Enum


class EscalationStage(str, Enum):
    STAGE_1 = "stage_1"   # 1–7 days overdue  — Warm & Friendly
    STAGE_2 = "stage_2"   # 8–14 days overdue — Polite but Firm
    STAGE_3 = "stage_3"   # 15–21 days overdue — Formal & Serious
    STAGE_4 = "stage_4"   # 22–30 days overdue — Stern & Urgent
    ESCALATED = "escalated"  # 30+ days — Flag for Legal


class InvoiceRecord(BaseModel):
    invoice_no: str
    client_name: str
    client_email: str
    amount: float
    currency: str = "INR"
    due_date: str           # ISO format YYYY-MM-DD
    days_overdue: int
    follow_up_count: int
    payment_link: str
    contact_phone: str
    account_manager: str

    @field_validator("days_overdue")
    @classmethod
    def days_must_be_positive(cls, v):
        if v < 0:
            raise ValueError("days_overdue must be >= 0")
        return v

    @field_validator("client_email")
    @classmethod
    def email_must_be_valid(cls, v):
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError(f"Invalid email: {v}")
        return v.lower().strip()


class GeneratedEmail(BaseModel):
    invoice_no: str
    client_name: str
    client_email: str
    stage: EscalationStage
    subject: str
    body: str
    tone: str
    days_overdue: int
    amount: float
    currency: str

    @field_validator("subject", "body")
    @classmethod
    def must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Email subject/body must not be empty")
        return v.strip()


class AuditEntry(BaseModel):
    timestamp: str
    invoice_no: str
    client_name: str
    client_email: str
    amount: float
    currency: str
    days_overdue: int
    stage: str
    tone: str
    subject: str
    send_status: str          # "sent" | "dry_run" | "escalated" | "error"
    error_message: Optional[str] = None
