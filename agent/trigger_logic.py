"""
trigger_logic.py
────────────────
Orchestrates the full agent loop:
  1. Load invoice records
  2. Filter overdue invoices
  3. Determine escalation stage per invoice
  4. Generate personalised email via LLM (unless escalated)
  5. Send / dry-run the email
  6. Write audit log entry

This is intentionally a simple sequential loop — no external agent
framework required for a prototype. Each step is logged individually
so partial failures don't abort the entire run.
"""

from typing import List
from models.schemas import InvoiceRecord, EscalationStage
from agent.escalation_engine import get_stage
from agent.email_generator import generate_email
from agent.audit_logger import log_entry, log_escalation
from utils.data_loader import load_invoices, filter_overdue
from utils.email_sender import send_email
import config


def run_agent(data_file: str = None, dry_run_override: bool = False) -> dict:
    """
    Execute the full follow-up agent pipeline.

    Args:
        data_file         : Path to CSV/Excel (defaults to config.DATA_FILE)
        dry_run_override  : Force dry-run regardless of EMAIL_MODE setting

    Returns:
        Summary dict with counts: sent, escalated, errors, skipped
    """
    summary = {"sent": 0, "escalated": 0, "errors": 0, "skipped": 0, "total": 0}

    print(f"\n{'█'*60}")
    print(f"  Finance Follow-Up Agent — {config.COMPANY_NAME}")
    print(f"  LLM Model  : {config.LLM_MODEL}")
    print(f"  Email Mode : {'DRY RUN' if dry_run_override else config.EMAIL_MODE.upper()}")
    print(f"{'█'*60}\n")

    # ── 1. Load & filter ──────────────────────────────────────────────────────
    all_records: List[InvoiceRecord] = load_invoices(data_file)
    overdue: List[InvoiceRecord] = filter_overdue(all_records)
    summary["total"] = len(overdue)

    if not overdue:
        print("[Agent] No overdue invoices found. Exiting.")
        return summary

    # ── 2. Process each overdue invoice ───────────────────────────────────────
    for invoice in overdue:
        stage = get_stage(invoice)
        print(f"\n[Agent] Processing {invoice.invoice_no} | {invoice.client_name} "
              f"| {invoice.days_overdue}d overdue → Stage: {stage.value.upper()}")

        # ── Escalation flag (no email) ────────────────────────────────────────
        if stage == EscalationStage.ESCALATED:
            print(f"  ⚠  FLAGGED for manual review (>{30}d overdue)")
            log_escalation(
                invoice_no=invoice.invoice_no,
                client_name=invoice.client_name,
                client_email=invoice.client_email,
                amount=invoice.amount,
                currency=invoice.currency,
                days_overdue=invoice.days_overdue,
            )
            summary["escalated"] += 1
            continue

        # ── Generate email via LLM ────────────────────────────────────────────
        try:
            generated = generate_email(invoice, stage)
            print(f"  ✓  Email generated — Subject: {generated.subject[:60]}...")
        except Exception as exc:
            print(f"  ✗  LLM generation failed: {exc}")
            summary["errors"] += 1
            continue

        # ── Send / dry-run ────────────────────────────────────────────────────
        if dry_run_override:
            # Force dry-run regardless of global config
            original_mode = config.EMAIL_MODE
            config.EMAIL_MODE = "dry_run"
            success, status = send_email(generated)
            config.EMAIL_MODE = original_mode
        else:
            success, status = send_email(generated)

        # ── Audit log ─────────────────────────────────────────────────────────
        log_entry(
            email=generated,
            send_status=status,
            error_message=None if success else status,
        )

        if success:
            summary["sent"] += 1
            print(f"  ✓  Logged — status: {status}")
        else:
            summary["errors"] += 1
            print(f"  ✗  Send failed — {status}")

    # ── 3. Print summary ──────────────────────────────────────────────────────
    print(f"\n{'─'*60}")
    print(f"  Run Complete")
    print(f"  Total overdue  : {summary['total']}")
    print(f"  Emails sent    : {summary['sent']}")
    print(f"  Escalated      : {summary['escalated']}")
    print(f"  Errors         : {summary['errors']}")
    print(f"  Audit log      : {config.AUDIT_JSON}")
    print(f"  Audit DB       : {config.AUDIT_DB}")
    print(f"{'─'*60}\n")

    return summary
