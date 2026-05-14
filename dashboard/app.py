"""
dashboard/app.py — Streamlit UI for the Finance Follow-Up Agent

Run with:
    streamlit run dashboard/app.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
from datetime import datetime

import config
from agent.audit_logger import get_all_entries
from agent.trigger_logic import run_agent
from utils.data_loader import load_invoices, filter_overdue
from agent.escalation_engine import get_stage, STAGE_META

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Finance Follow-Up Agent",
    page_icon="💼",
    layout="wide",
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("⚙️ Agent Controls")

data_file = st.sidebar.text_input("Invoice CSV/Excel path", value=config.DATA_FILE)
dry_run   = st.sidebar.checkbox("Dry-run mode (no real emails)", value=True)

run_clicked = st.sidebar.button("▶ Run Agent", type="primary", use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.markdown(f"**LLM Model:** `{config.LLM_MODEL}`")
st.sidebar.markdown(f"**Email Mode:** `{'DRY RUN' if dry_run else config.EMAIL_MODE}`")
st.sidebar.markdown(f"**Company:** {config.COMPANY_NAME}")

# ── Header ────────────────────────────────────────────────────────────────────
st.title("💼 Finance Follow-Up Agent Dashboard")
st.caption(f"AI-powered overdue invoice follow-up  •  {config.COMPANY_NAME}")

# ── Run agent ─────────────────────────────────────────────────────────────────
if run_clicked:
    with st.spinner("Running agent…"):
        issues = config.validate_config()
        if issues:
            for i in issues:
                st.error(f"Config error: {i}")
        else:
            summary = run_agent(data_file=data_file, dry_run_override=dry_run)
            st.success(
                f"✅ Run complete — Sent: **{summary['sent']}**  |  "
                f"Escalated: **{summary['escalated']}**  |  "
                f"Errors: **{summary['errors']}**"
            )

# ── Queue overview ────────────────────────────────────────────────────────────
st.subheader("📋 Invoice Queue")
try:
    records = load_invoices(data_file)
    overdue = filter_overdue(records)
    rows = []
    for inv in records:
        stage = get_stage(inv) if inv.days_overdue > 0 else None
        stage_label = STAGE_META[stage]["label"] if stage else "Current"
        tone = STAGE_META[stage]["tone"] if stage else "—"
        rows.append({
            "Invoice":       inv.invoice_no,
            "Client":        inv.client_name,
            "Amount":        f"{inv.currency} {inv.amount:,.2f}",
            "Due Date":      inv.due_date,
            "Days Overdue":  inv.days_overdue,
            "Stage":         stage_label,
            "Tone":          tone,
        })
    queue_df = pd.DataFrame(rows)

    def colour_row(row):
        d = row["Days Overdue"]
        if d > 30:  return ["background-color: #ffd6d6"] * len(row)
        if d >= 22: return ["background-color: #ffe8cc"] * len(row)
        if d >= 15: return ["background-color: #fff3cc"] * len(row)
        if d >= 8:  return ["background-color: #e8f4e8"] * len(row)
        if d >= 1:  return ["background-color: #e8f0ff"] * len(row)
        return [""] * len(row)

    st.dataframe(queue_df.style.apply(colour_row, axis=1), use_container_width=True)
except Exception as exc:
    st.warning(f"Could not load invoice data: {exc}")

# ── Metric cards ──────────────────────────────────────────────────────────────
st.subheader("📊 Summary Metrics")
try:
    all_inv = load_invoices(data_file)
    overdue_inv = filter_overdue(all_inv)
    stage_counts = {}
    from models.schemas import EscalationStage
    for inv in overdue_inv:
        s = get_stage(inv)
        stage_counts[s.value] = stage_counts.get(s.value, 0) + 1

    cols = st.columns(5)
    for i, (key, label) in enumerate([
        ("stage_1", "🟢 Stage 1"),
        ("stage_2", "🟡 Stage 2"),
        ("stage_3", "🟠 Stage 3"),
        ("stage_4", "🔴 Stage 4"),
        ("escalated", "⛔ Escalated"),
    ]):
        cols[i].metric(label, stage_counts.get(key, 0))
except Exception as exc:
    st.warning(f"Could not calculate metrics: {exc}")

# ── Audit log ─────────────────────────────────────────────────────────────────
st.subheader("🗂 Audit Trail")
entries = get_all_entries()
if entries:
    audit_df = pd.DataFrame(entries).drop(columns=["id"], errors="ignore")
    st.dataframe(audit_df, use_container_width=True)
    csv_data = audit_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇ Download Audit Log (CSV)",
        data=csv_data,
        file_name=f"audit_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )
else:
    st.info("No audit records yet. Run the agent to populate the log.")

# ── Escalation alerts ─────────────────────────────────────────────────────────
escalated = [e for e in entries if e.get("stage") == "escalated"]
if escalated:
    st.subheader("⚠️ Records Flagged for Legal / Finance Review")
    esc_df = pd.DataFrame(escalated)[
        ["timestamp", "invoice_no", "client_name", "client_email", "amount", "days_overdue"]
    ]
    st.error(f"{len(escalated)} invoice(s) require manual review.")
    st.dataframe(esc_df, use_container_width=True)
