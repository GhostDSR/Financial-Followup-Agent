"""
audit_logger.py
───────────────
Logs every agent action to:
  1. SQLite database  (logs/audit.db)    — structured, queryable
  2. JSON append log  (logs/audit_log.json) — portable, human-readable

Security note: Email body is NOT stored in the audit log to avoid
retaining PII-heavy content unnecessarily. Only metadata is persisted.
"""

import sqlite3
import json
import os
from datetime import datetime, timezone

import config
from models.schemas import AuditEntry, GeneratedEmail, EscalationStage


def _ensure_dirs():
    os.makedirs(os.path.dirname(config.AUDIT_DB), exist_ok=True)
    os.makedirs(os.path.dirname(config.AUDIT_JSON), exist_ok=True)


def _get_conn() -> sqlite3.Connection:
    _ensure_dirs()
    conn = sqlite3.connect(config.AUDIT_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp       TEXT NOT NULL,
            invoice_no      TEXT NOT NULL,
            client_name     TEXT NOT NULL,
            client_email    TEXT NOT NULL,
            amount          REAL NOT NULL,
            currency        TEXT NOT NULL,
            days_overdue    INTEGER NOT NULL,
            stage           TEXT NOT NULL,
            tone            TEXT NOT NULL,
            subject         TEXT NOT NULL,
            send_status     TEXT NOT NULL,
            error_message   TEXT
        )
    """)
    conn.commit()
    return conn


def log_entry(
    email: GeneratedEmail,
    send_status: str,
    error_message: str = None,
) -> AuditEntry:
    """
    Persist one audit record to SQLite and the JSON log file.
    Returns the AuditEntry for downstream use.
    """
    entry = AuditEntry(
        timestamp=datetime.now(timezone.utc).isoformat(),
        invoice_no=email.invoice_no,
        client_name=email.client_name,
        client_email=email.client_email,
        amount=email.amount,
        currency=email.currency,
        days_overdue=email.days_overdue,
        stage=email.stage.value,
        tone=email.tone,
        subject=email.subject,
        send_status=send_status,
        error_message=error_message,
    )

    # ── SQLite ────────────────────────────────────────────────────────────────
    try:
        conn = _get_conn()
        conn.execute(
            """INSERT INTO audit_log
               (timestamp, invoice_no, client_name, client_email, amount, currency,
                days_overdue, stage, tone, subject, send_status, error_message)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                entry.timestamp, entry.invoice_no, entry.client_name,
                entry.client_email, entry.amount, entry.currency,
                entry.days_overdue, entry.stage, entry.tone, entry.subject,
                entry.send_status, entry.error_message,
            ),
        )
        conn.commit()
        conn.close()
    except Exception as exc:
        print(f"[AuditLogger] SQLite write failed: {exc}")

    # ── JSON append ───────────────────────────────────────────────────────────
    try:
        _ensure_dirs()
        with open(config.AUDIT_JSON, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry.model_dump()) + "\n")
    except Exception as exc:
        print(f"[AuditLogger] JSON write failed: {exc}")

    return entry


def log_escalation(invoice_no: str, client_name: str, client_email: str,
                   amount: float, currency: str, days_overdue: int) -> None:
    """Log a manual-review escalation flag (no email sent)."""
    _ensure_dirs()
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "invoice_no": invoice_no,
        "client_name": client_name,
        "client_email": client_email,
        "amount": amount,
        "currency": currency,
        "days_overdue": days_overdue,
        "stage": EscalationStage.ESCALATED.value,
        "tone": "N/A",
        "subject": "FLAGGED FOR LEGAL/FINANCE REVIEW",
        "send_status": "escalated",
        "error_message": None,
    }
    try:
        conn = _get_conn()
        conn.execute(
            """INSERT INTO audit_log
               (timestamp, invoice_no, client_name, client_email, amount, currency,
                days_overdue, stage, tone, subject, send_status, error_message)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            tuple(record.values()),
        )
        conn.commit()
        conn.close()
    except Exception as exc:
        print(f"[AuditLogger] Escalation SQLite write failed: {exc}")

    try:
        with open(config.AUDIT_JSON, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception as exc:
        print(f"[AuditLogger] Escalation JSON write failed: {exc}")


def get_all_entries() -> list[dict]:
    """Fetch all audit log rows as a list of dicts (used by Streamlit dashboard)."""
    try:
        conn = _get_conn()
        cur = conn.execute("SELECT * FROM audit_log ORDER BY id DESC")
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]
        conn.close()
        return rows
    except Exception:
        return []
