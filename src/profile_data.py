"""PROFILE step: measure the problems in the raw data BEFORE cleaning.

Run from the project root:
    python -m src.profile_data
"""
import sys

import pandas as pd

from src.extract import extract


def profile(df: pd.DataFrame) -> dict:
    """Count each kind of problem in the raw data and return the numbers."""
    quantity = pd.to_numeric(df["Quantity"], errors="coerce")
    price = pd.to_numeric(df["Price"], errors="coerce")
    dates = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    invoice = df["Invoice"].astype(str)

    return {
        "rows": len(df),
        "columns": df.shape[1],
        "date_min": str(dates.min()),
        "date_max": str(dates.max()),
        "duplicate_rows": int(df.duplicated().sum()),
        "missing_customer_id": int(df["Customer ID"].isna().sum()),
        "missing_description": int(df["Description"].isna().sum()),
        "quantity_below_zero": int((quantity < 0).sum()),
        "quantity_equal_zero": int((quantity == 0).sum()),
        "price_below_zero": int((price < 0).sum()),
        "price_equal_zero": int((price == 0).sum()),
        "cancelled_invoices": int(invoice.str.startswith("C").sum()),
        "invalid_dates": int(dates.isna().sum()),
    }


def print_profile(result: dict) -> None:
    rows = max(result["rows"], 1)
    print("RAW DATA PROFILE")
    print("=" * 46)
    print(f"Rows: {result['rows']:,}   Columns: {result['columns']}")
    print(f"Date range: {result['date_min']} to {result['date_max']}")
    print()
    labels = [
        ("Duplicate rows", "duplicate_rows"),
        ("Missing Customer ID", "missing_customer_id"),
        ("Missing Description", "missing_description"),
        ("Quantity below zero", "quantity_below_zero"),
        ("Quantity equal to zero", "quantity_equal_zero"),
        ("Price below zero", "price_below_zero"),
        ("Price equal to zero", "price_equal_zero"),
        ("Cancelled invoices (C...)", "cancelled_invoices"),
        ("Invalid dates", "invalid_dates"),
    ]
    for label, key in labels:
        n = result[key]
        print(f"{label:<28}{n:>10,}  ({n / rows:.2%})")


if __name__ == "__main__":
    data = extract(sys.argv[1]) if len(sys.argv) > 1 else extract()
    print_profile(profile(data))