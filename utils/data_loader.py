import pandas as pd
from datetime import date, datetime
from typing import List
from models.schemas import InvoiceRecord
import config


def load_invoices(filepath: str = None) -> List[InvoiceRecord]:
    """
    Load invoice records from CSV/Excel and return a validated list of InvoiceRecord objects.
    Automatically recalculates days_overdue from due_date if a live run is needed.
    """
    filepath = filepath or config.DATA_FILE
    if filepath.endswith((".xlsx", ".xls")):
        df = pd.read_excel(filepath)
    else:
        df = pd.read_csv(filepath)

    # Normalise column names
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Recalculate days_overdue from due_date (live mode)
    if "due_date" in df.columns:
        df["due_date"] = pd.to_datetime(df["due_date"]).dt.date
        today = date.today()
        df["days_overdue"] = df["due_date"].apply(
            lambda d: max((today - d).days, 0)
        )
        df["due_date"] = df["due_date"].astype(str)

    # Fill optional columns with defaults
    df["follow_up_count"] = df.get("follow_up_count", pd.Series([0] * len(df))).fillna(0).astype(int)
    df["currency"] = df.get("currency", pd.Series(["INR"] * len(df))).fillna("INR")
    df["payment_link"] = df.get("payment_link", pd.Series([""] * len(df))).fillna("")
    df["contact_phone"] = df.get("contact_phone", pd.Series([""] * len(df))).fillna("")
    df["account_manager"] = df.get("account_manager", pd.Series(["Finance Team"] * len(df))).fillna("Finance Team")

    records: List[InvoiceRecord] = []
    for _, row in df.iterrows():
        try:
            record = InvoiceRecord(
                invoice_no=str(row["invoice_no"]),
                client_name=str(row["client_name"]),
                client_email=str(row["client_email"]),
                amount=float(row["amount"]),
                currency=str(row["currency"]),
                due_date=str(row["due_date"]),
                days_overdue=int(row["days_overdue"]),
                follow_up_count=int(row["follow_up_count"]),
                payment_link=str(row["payment_link"]),
                contact_phone=str(row["contact_phone"]),
                account_manager=str(row["account_manager"]),
            )
            records.append(record)
        except Exception as e:
            print(f"[DataLoader] Skipping row {row.get('invoice_no', '?')}: {e}")

    print(f"[DataLoader] Loaded {len(records)} valid invoice records from '{filepath}'")
    return records


def filter_overdue(records: List[InvoiceRecord]) -> List[InvoiceRecord]:
    """Return only records that are overdue (days_overdue > 0)."""
    overdue = [r for r in records if r.days_overdue > 0]
    print(f"[DataLoader] {len(overdue)} overdue records identified")
    return overdue
