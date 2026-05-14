from models.schemas import EscalationStage, InvoiceRecord


# ── Stage metadata ──────────────────────────────────────────────────────────────
STAGE_META: dict[EscalationStage, dict] = {
    EscalationStage.STAGE_1: {
        "label": "1st Follow-Up",
        "tone": "Warm & Friendly",
        "days_range": "1–7 days overdue",
        "key_message": "Gentle reminder — assume oversight",
        "cta": "Pay now via the payment link / bank details provided",
    },
    EscalationStage.STAGE_2: {
        "label": "2nd Follow-Up",
        "tone": "Polite but Firm",
        "days_range": "8–14 days overdue",
        "key_message": "Payment still pending; request confirmation",
        "cta": "Confirm payment date",
    },
    EscalationStage.STAGE_3: {
        "label": "3rd Follow-Up",
        "tone": "Formal & Serious",
        "days_range": "15–21 days overdue",
        "key_message": "Escalating concern; mention impact on credit terms",
        "cta": "Respond within 48 hours",
    },
    EscalationStage.STAGE_4: {
        "label": "4th Follow-Up",
        "tone": "Stern & Urgent",
        "days_range": "22–30 days overdue",
        "key_message": "Final reminder before legal escalation",
        "cta": "Pay immediately or call us",
    },
    EscalationStage.ESCALATED: {
        "label": "Escalation Flag",
        "tone": "N/A — Human Review",
        "days_range": "30+ days overdue",
        "key_message": "Human review required; no auto email",
        "cta": "Assign to finance manager / legal team",
    },
}


def get_stage(invoice: InvoiceRecord) -> EscalationStage:
    """
    Determine the correct escalation stage based purely on days_overdue.
    This ensures tone always matches actual elapsed time, not just follow-up count.
    """
    d = invoice.days_overdue
    if d > 30:
        return EscalationStage.ESCALATED
    elif d >= 22:
        return EscalationStage.STAGE_4
    elif d >= 15:
        return EscalationStage.STAGE_3
    elif d >= 8:
        return EscalationStage.STAGE_2
    elif d >= 1:
        return EscalationStage.STAGE_1
    else:
        return EscalationStage.STAGE_1   # edge case: 0 days — send stage 1


def get_stage_meta(stage: EscalationStage) -> dict:
    return STAGE_META[stage]
