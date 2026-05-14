# 💼 Finance Follow-Up Email Agent

An AI-powered agent that automatically generates and dispatches personalised follow-up emails for overdue invoices — with tone escalation from warm reminder to stern final notice, a Streamlit dashboard, full audit logging, and dry-run safety mode.

---

## ✨ Features

| Feature | Description |
|---|---|
| **Tone Escalation Engine** | 4-stage matrix (Warm → Firm → Formal → Stern) driven by days overdue |
| **LLM Email Generation** | Claude Sonnet 4 generates personalised, structured emails per invoice |
| **Escalation Cap** | 30+ days overdue → flagged for legal/finance review, no auto-email |
| **Dry-Run Mode** | Default safe mode — previews emails without sending |
| **Multi-channel Send** | SMTP, SendGrid, or dry-run log |
| **Audit Trail** | Every action logged to SQLite + JSON with timestamp, stage, status |
| **Streamlit Dashboard** | Visual queue, metrics by stage, audit log viewer, download CSV |
| **Scheduled Runs** | APScheduler cron (daily 9 AM by default) |
| **Data Sources** | CSV or Excel via pandas |

---

## 🗂 Project Structure

```
finance-followup-agent/
├── main.py                    # CLI entry point
├── scheduler.py               # APScheduler daily cron
├── config.py                  # Env var loader & validation
├── requirements.txt
├── .env.example               # Template — copy to .env
├── .gitignore
│
├── agent/
│   ├── escalation_engine.py   # Stage/tone mapping logic
│   ├── email_generator.py     # Anthropic Claude LLM calls
│   ├── audit_logger.py        # SQLite + JSON audit trail
│   └── trigger_logic.py       # Main orchestration loop
│
├── models/
│   └── schemas.py             # Pydantic models (InvoiceRecord, GeneratedEmail, AuditEntry)
│
├── utils/
│   ├── data_loader.py         # CSV/Excel → InvoiceRecord list
│   └── email_sender.py        # SMTP / SendGrid / dry-run
│
├── data/
│   └── sample_invoices.csv    # 8 sample records for testing
│
├── dashboard/
│   └── app.py                 # Streamlit UI
│
├── docs/
│   └── TECH_STACK.md          # Full technical decision log
│
├── tests/
│   └── test_agent.py          # Pytest unit tests
│
└── logs/                      # Auto-created on first run
    ├── audit.db               # SQLite audit database
    └── audit_log.json         # JSON audit trail (append)
```

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/finance-followup-agent.git
cd finance-followup-agent
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY at minimum
```

### 5. Run in dry-run mode (safe — no emails sent)

```bash
python main.py
```

### 6. Run with real email delivery

```bash
python main.py --send
```

### 7. Use a custom data file

```bash
python main.py --file path/to/invoices.xlsx
python main.py --file path/to/invoices.csv --send
```

---

## 📊 Streamlit Dashboard

```bash
streamlit run dashboard/app.py
```

Opens at `http://localhost:8501`. Features:
- Colour-coded invoice queue (green → yellow → orange → red → critical)
- Stage metric cards
- Run the agent directly from the UI
- Full audit log table with CSV export
- Escalation alerts panel

---

## 🔔 Tone Escalation Matrix

| Stage | Trigger | Tone | Key Message | CTA |
|---|---|---|---|---|
| **Stage 1** | 1–7 days overdue | Warm & Friendly | Gentle reminder, assume oversight | Pay via link |
| **Stage 2** | 8–14 days overdue | Polite but Firm | Payment still pending | Confirm payment date |
| **Stage 3** | 15–21 days overdue | Formal & Serious | Escalating concern; mention credit impact | Respond within 48 hrs |
| **Stage 4** | 22–30 days overdue | Stern & Urgent | Final reminder before escalation | Pay immediately or call |
| **Escalated** | 30+ days | ⚠️ No auto-email | Flagged for legal/finance review | Assign to manager |

---

## 📧 Sample Email Output

**Stage 1 — Warm & Friendly:**
```
Subject: Quick Reminder – Invoice #INV-2024-001 | INR 45,000.00 Due

Hi Rajesh,

I hope you're doing well! This is a friendly reminder that Invoice #INV-2024-001
for INR 45,000.00 was due on 20 Apr 2025, and appears to still be outstanding.

We understand things can get busy — if you've already processed this payment,
please disregard this message. Otherwise, you can complete payment using the link
below:

👉 https://pay.example.com/INV-2024-001

If you have any questions, feel free to reach out at finance@yourcompany.com
or +91-11-2345-6789.

Thank you for your continued partnership!

Warm regards,
Finance Team | Acme Corp
```

**Stage 4 — Stern & Urgent:**
```
Subject: FINAL NOTICE – Invoice #INV-2024-005 – Immediate Action Required

Dear Mr. Singh,

This is our final reminder regarding Invoice #INV-2024-005 for INR 2,30,000.00,
which is now 29 days overdue since 15 Apr 2025.

Despite our previous communications, payment has not been received. Failure to
remit payment within 24 hours will necessitate escalation to our legal and
recovery team, which may impact your credit terms and result in additional costs.

Please act immediately:
👉 https://pay.example.com/INV-2024-005

Or contact us directly: +91-54321-09876

Regards,
Finance Team | Acme Corp
```

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

Tests cover:
- Escalation stage boundary conditions (all 5 stages)
- Pydantic schema validation (invalid email, negative days, empty fields)
- LLM email generator with mocked Anthropic client
- Data loader CSV parsing and overdue filtering

---

## ⏰ Scheduled Runs

```bash
python scheduler.py
```

Runs immediately, then daily at 09:00. Edit `CRON_HOUR` / `CRON_MINUTE` in `scheduler.py` to adjust.

For production, consider running via:
- **GitHub Actions:** `.github/workflows/daily_run.yml` with cron schedule
- **Celery + Redis:** For distributed task queuing
- **systemd timer:** On a Linux server

---

## 🔐 Security

See [`docs/TECH_STACK.md`](docs/TECH_STACK.md) for full security documentation. Summary:

| Risk | Mitigation |
|---|---|
| Prompt Injection | Regex sanitisation on all client-supplied fields |
| PII in Logs | Email body not stored; only metadata persisted |
| API Key Exposure | `.env` + `python-dotenv`; `.env` in `.gitignore` |
| Hallucination | Structured JSON output + Pydantic validation; source fields never re-extracted from LLM output |
| Unauthorised Access | Dry-run default; `--send` flag required for real delivery |
| Email Spoofing | SPF/DKIM/DMARC recommended; verified sender domain required |

---

## 🛠 Tech Stack

| Layer | Choice | Version |
|---|---|---|
| LLM | Claude Sonnet 4 (Anthropic) | `claude-sonnet-4-20250514` |
| Agent Framework | Custom sequential loop | — |
| Data Ingestion | pandas + openpyxl | ≥2.0 |
| Validation | Pydantic v2 | ≥2.5 |
| Email (SMTP) | smtplib (stdlib) | — |
| Email (cloud) | SendGrid | ≥6.11 |
| Audit Storage | SQLite + JSON | stdlib |
| Dashboard | Streamlit | ≥1.35 |
| Scheduling | APScheduler | ≥3.10 |
| Testing | pytest + pytest-mock | ≥8.0 |

---

## 📋 Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ | — | Anthropic API key |
| `LLM_MODEL` | | `claude-sonnet-4-20250514` | Model to use |
| `EMAIL_MODE` | | `dry_run` | `dry_run` / `smtp` / `sendgrid` |
| `SMTP_HOST` | smtp only | `smtp.gmail.com` | SMTP server |
| `SMTP_USER` | smtp only | — | SMTP login |
| `SMTP_PASSWORD` | smtp only | — | SMTP app password |
| `SENDGRID_API_KEY` | sendgrid only | — | SendGrid API key |
| `FROM_EMAIL` | | `finance@yourcompany.com` | Sender email |
| `DATA_FILE` | | `data/sample_invoices.csv` | Invoice data path |
| `COMPANY_NAME` | | `Acme Corp` | Used in email sign-off |

---

## 📦 Input Data Format

CSV/Excel columns (column names are case-insensitive):

| Column | Type | Required | Description |
|---|---|---|---|
| `invoice_no` | string | ✅ | Unique invoice identifier |
| `client_name` | string | ✅ | Debtor's full name |
| `client_email` | string | ✅ | Debtor's email address |
| `amount` | float | ✅ | Amount due |
| `due_date` | date (YYYY-MM-DD) | ✅ | Original due date |
| `currency` | string | | Default: INR |
| `follow_up_count` | int | | Default: 0 |
| `payment_link` | string | | Payment portal URL |
| `contact_phone` | string | | Your company's contact |
| `account_manager` | string | | Assigned account manager |

> `days_overdue` is auto-calculated from `due_date` vs today's date at runtime.

---

## 📄 License

MIT License. See `LICENSE` for details.
