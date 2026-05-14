"""
email_generator.py
──────────────────
Uses the Anthropic Claude API to generate personalised, structured follow-up
emails for each debtor. Returns a validated GeneratedEmail Pydantic object.

Security mitigations applied:
  • Input sanitisation  – strip/escape client-supplied fields before injection
  • Structured output   – LLM must return JSON; parsed via Pydantic
  • Guardrail checks    – reject responses that omit mandatory fields
  • No PII in logs      – email body is logged only at DEBUG level
"""

import json
import re
import anthropic

import config
from models.schemas import EscalationStage, GeneratedEmail, InvoiceRecord
from agent.escalation_engine import get_stage_meta

# ── Anthropic client (key from env, never hardcoded) ───────────────────────────
_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


# ── Input sanitisation ─────────────────────────────────────────────────────────
_INJECTION_PATTERNS = re.compile(
    r"(ignore previous|disregard|system prompt|jailbreak|forget instructions)",
    re.IGNORECASE,
)

def _sanitise(value: str) -> str:
    """Strip leading/trailing whitespace and reject prompt-injection attempts."""
    cleaned = str(value).strip()
    if _INJECTION_PATTERNS.search(cleaned):
        raise ValueError(f"Potential prompt injection detected in field: '{cleaned[:40]}...'")
    return cleaned


# ── System prompt ──────────────────────────────────────────────────────────────
_SYSTEM_PROMPT = """You are a professional finance communication assistant for {company_name}.
Your task is to draft follow-up emails for overdue invoices.

RULES (mandatory — never deviate):
1. Return ONLY a valid JSON object with these exact keys:
   subject, body
2. Do NOT include any text outside the JSON object.
3. Do NOT use markdown fences (``` etc.) around the JSON.
4. Populate every email with the exact client name, invoice number, amount, due date,
   days overdue, and payment link provided — never invent or omit any of these.
5. Match the tone strictly as instructed. Do not add disclaimers or apologies for the tone.
6. Keep the body professional, concise (150–250 words), and free from threats of violence.
7. Never suggest, imply, or generate illegal actions.
""".format(company_name=config.COMPANY_NAME)


# ── User prompt template ───────────────────────────────────────────────────────
def _build_user_prompt(invoice: InvoiceRecord, stage: EscalationStage) -> str:
    meta = get_stage_meta(stage)
    amount_fmt = f"{invoice.currency} {invoice.amount:,.2f}"
    return f"""Generate a follow-up email using the details below.

INVOICE DETAILS:
- Client Name      : {_sanitise(invoice.client_name)}
- Invoice Number   : {_sanitise(invoice.invoice_no)}
- Amount Due       : {amount_fmt}
- Due Date         : {_sanitise(invoice.due_date)}
- Days Overdue     : {invoice.days_overdue}
- Payment Link     : {_sanitise(invoice.payment_link)}
- Contact Phone    : {_sanitise(invoice.contact_phone)}
- Account Manager  : {_sanitise(invoice.account_manager)}
- Our Company      : {config.COMPANY_NAME}
- Our Email        : {config.COMPANY_EMAIL}

TONE & STAGE:
- Stage            : {meta['label']}
- Tone             : {meta['tone']}
- Key Message      : {meta['key_message']}
- Call To Action   : {meta['cta']}

OUTPUT FORMAT (strict):
{{
  "subject": "<email subject line>",
  "body": "<full email body with greeting and sign-off>"
}}"""


# ── Main generator ─────────────────────────────────────────────────────────────
def generate_email(invoice: InvoiceRecord, stage: EscalationStage) -> GeneratedEmail:
    """
    Call the LLM and return a validated GeneratedEmail.
    Raises ValueError if the LLM response cannot be parsed or validated.
    """
    prompt = _build_user_prompt(invoice, stage)
    meta = get_stage_meta(stage)

    response = _client.messages.create(
        model=config.LLM_MODEL,
        max_tokens=config.LLM_MAX_TOKENS,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = response.content[0].text.strip()

    # ── Parse & validate JSON output ──────────────────────────────────────────
    try:
        # Strip accidental markdown fences
        raw_text = re.sub(r"^```[a-z]*\n?", "", raw_text)
        raw_text = re.sub(r"\n?```$", "", raw_text)
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM returned non-JSON output: {exc}\nRaw: {raw_text[:200]}")

    if "subject" not in parsed or "body" not in parsed:
        raise ValueError(f"LLM response missing required keys. Got: {list(parsed.keys())}")

    return GeneratedEmail(
        invoice_no=invoice.invoice_no,
        client_name=invoice.client_name,
        client_email=invoice.client_email,
        stage=stage,
        subject=parsed["subject"],
        body=parsed["body"],
        tone=meta["tone"],
        days_overdue=invoice.days_overdue,
        amount=invoice.amount,
        currency=invoice.currency,
    )
