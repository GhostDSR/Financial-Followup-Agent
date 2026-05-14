"""
tests/test_agent.py — Unit tests for the Finance Follow-Up Agent
Run with:  pytest tests/ -v
"""

import pytest
from unittest.mock import patch, MagicMock

from models.schemas import InvoiceRecord, EscalationStage, GeneratedEmail
from agent.escalation_engine import get_stage, get_stage_meta


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_invoice(days_overdue: int, follow_up_count: int = 0) -> InvoiceRecord:
    return InvoiceRecord(
        invoice_no="INV-TEST-001",
        client_name="Test Client",
        client_email="test@example.com",
        amount=10000.0,
        currency="INR",
        due_date="2025-04-01",
        days_overdue=days_overdue,
        follow_up_count=follow_up_count,
        payment_link="https://pay.example.com/test",
        contact_phone="+91-99999-00000",
        account_manager="Test Manager",
    )


# ── Escalation engine ─────────────────────────────────────────────────────────

class TestEscalationEngine:
    def test_stage_1_boundary_low(self):
        assert get_stage(make_invoice(1)) == EscalationStage.STAGE_1

    def test_stage_1_boundary_high(self):
        assert get_stage(make_invoice(7)) == EscalationStage.STAGE_1

    def test_stage_2_boundary_low(self):
        assert get_stage(make_invoice(8)) == EscalationStage.STAGE_2

    def test_stage_2_boundary_high(self):
        assert get_stage(make_invoice(14)) == EscalationStage.STAGE_2

    def test_stage_3_boundary_low(self):
        assert get_stage(make_invoice(15)) == EscalationStage.STAGE_3

    def test_stage_3_boundary_high(self):
        assert get_stage(make_invoice(21)) == EscalationStage.STAGE_3

    def test_stage_4_boundary_low(self):
        assert get_stage(make_invoice(22)) == EscalationStage.STAGE_4

    def test_stage_4_boundary_high(self):
        assert get_stage(make_invoice(30)) == EscalationStage.STAGE_4

    def test_escalated(self):
        assert get_stage(make_invoice(31)) == EscalationStage.ESCALATED

    def test_escalated_far_overdue(self):
        assert get_stage(make_invoice(90)) == EscalationStage.ESCALATED

    def test_stage_meta_has_required_keys(self):
        for stage in EscalationStage:
            meta = get_stage_meta(stage)
            assert "tone" in meta
            assert "label" in meta
            assert "cta" in meta


# ── Schema validation ─────────────────────────────────────────────────────────

class TestSchemas:
    def test_invalid_email_raises(self):
        with pytest.raises(Exception):
            InvoiceRecord(
                invoice_no="INV-001",
                client_name="X",
                client_email="not-an-email",
                amount=1000,
                currency="INR",
                due_date="2025-01-01",
                days_overdue=5,
                follow_up_count=0,
                payment_link="",
                contact_phone="",
                account_manager="",
            )

    def test_negative_days_overdue_raises(self):
        with pytest.raises(Exception):
            make_invoice(-1)

    def test_valid_invoice_creates_ok(self):
        inv = make_invoice(10)
        assert inv.invoice_no == "INV-TEST-001"
        assert inv.days_overdue == 10

    def test_generated_email_empty_subject_raises(self):
        with pytest.raises(Exception):
            GeneratedEmail(
                invoice_no="INV-001",
                client_name="X",
                client_email="x@example.com",
                stage=EscalationStage.STAGE_1,
                subject="",
                body="Some body",
                tone="Warm",
                days_overdue=5,
                amount=1000,
                currency="INR",
            )


# ── Email generator (mocked) ──────────────────────────────────────────────────

class TestEmailGenerator:
    @patch("agent.email_generator._client")
    def test_generate_email_returns_valid_object(self, mock_client):
        import json
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text=json.dumps({
                    "subject": "Test Subject",
                    "body": "Dear Test Client, please pay INV-TEST-001."
                })
            )
        ]
        mock_client.messages.create.return_value = mock_response

        from agent.email_generator import generate_email
        inv = make_invoice(5)
        result = generate_email(inv, EscalationStage.STAGE_1)

        assert isinstance(result, GeneratedEmail)
        assert result.subject == "Test Subject"
        assert result.stage == EscalationStage.STAGE_1

    @patch("agent.email_generator._client")
    def test_malformed_json_raises(self, mock_client):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="not json at all")]
        mock_client.messages.create.return_value = mock_response

        from agent.email_generator import generate_email
        with pytest.raises(ValueError, match="non-JSON"):
            generate_email(make_invoice(5), EscalationStage.STAGE_1)


# ── Data loader ───────────────────────────────────────────────────────────────

class TestDataLoader:
    def test_load_sample_csv(self):
        from utils.data_loader import load_invoices, filter_overdue
        records = load_invoices("data/sample_invoices.csv")
        assert len(records) > 0
        overdue = filter_overdue(records)
        assert all(r.days_overdue > 0 for r in overdue)

    def test_filter_overdue_excludes_current(self):
        from utils.data_loader import filter_overdue
        invoices = [make_invoice(0), make_invoice(5), make_invoice(15)]
        result = filter_overdue(invoices)
        assert len(result) == 2
