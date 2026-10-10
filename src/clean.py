"""CLEAN step: fix the data problems found while profiling.
Each cleaning rule gets a comment explaining WHY it exists.
(Built in Phase 3.)
"""
"""CLEAN step: fix the data problems found while profiling.

Every rule has a comment saying WHY it exists.
Rows we cannot trust are not silently deleted. They go to a "rejected"
table together with the reason, so nothing disappears without a trace.

Run from the project root:
    python -m src.clean
"""
import pandas as pd

from src.extract import extract

# SQL-friendly names ("Customer ID" has a space, which is awkward in SQL).
COLUMN_NAMES = {
    "Invoice": "invoice",
    "StockCode": "stock_code",
    "Description": "description",
    "Quantity": "quantity",
    "InvoiceDate": "invoice_date",
    "Price": "price",
    "Customer ID": "customer_id",
    "Country": "country",
}


def clean(df: pd.DataFrame):
    """Return (clean_df, rejected_df, stats)."""
    stats = {"rows_in": len(df)}

    # Rule 1: drop exact duplicate rows, keep the first copy.
    # Why: the same line counted twice would inflate revenue.
    deduped = df.drop_duplicates()
    stats["duplicates_removed"] = len(df) - len(deduped)
    df = deduped

    quantity = pd.to_numeric(df["Quantity"], errors="coerce")
    price = pd.to_numeric(df["Price"], errors="coerce")
    dates = pd.to_datetime(df["InvoiceDate"], errors="coerce")

    # Rules 2-6: a row that fails a rule goes to "rejected" with a reason.
    # Order matters: each row gets only its FIRST matching reason, so the
    # reasons add up exactly to the total number of rejected rows.
    rules = [
        # Invoices starting with "C" are cancellations/returns, not sales.
        ("cancelled_invoice", df["Invoice"].astype(str).str.startswith("C")),
        # A sale must have a positive quantity (this also catches non-numbers).
        ("non_positive_quantity", ~(quantity > 0)),
        # A sale must have a positive price (free items and adjustments are not sales).
        ("non_positive_price", ~(price > 0)),
        # Without a customer we cannot do customer-level analysis such as RFM.
        ("missing_customer_id", df["Customer ID"].isna()),
        # A sale must have a valid date.
        ("invalid_date", dates.isna()),
    ]
    reason = pd.Series(pd.NA, index=df.index, dtype="object")
    for name, mask in rules:
        reason = reason.mask(reason.isna() & mask, name)

    rejected = df[reason.notna()].copy()
    rejected["reject_reason"] = reason[reason.notna()]
    kept = df[reason.isna()].copy()

    # Rule 7 (a fix, not a removal): a missing description does not make a
    # sale wrong, so we label it instead of throwing the row away.
    kept["Description"] = kept["Description"].fillna("UNKNOWN")

    # Rule 8: use proper data types.
    kept["InvoiceDate"] = dates.loc[kept.index]
    kept["Quantity"] = quantity.loc[kept.index].astype(int)
    kept["Price"] = price.loc[kept.index]
    kept["Customer ID"] = kept["Customer ID"].astype(int)
    # Codes can contain letters (e.g. "POST"), so keep them as text.
    kept["Invoice"] = kept["Invoice"].astype(str)
    kept["StockCode"] = kept["StockCode"].astype(str)

    kept = kept.rename(columns=COLUMN_NAMES).reset_index(drop=True)
    rejected = rejected.rename(columns=COLUMN_NAMES).reset_index(drop=True)

    stats["rejected_by_reason"] = rejected["reject_reason"].value_counts().to_dict()
    stats["rows_rejected"] = len(rejected)
    stats["rows_clean"] = len(kept)

    # Safety check: every input row must be accounted for.
    assert stats["rows_in"] == (
        stats["duplicates_removed"] + stats["rows_rejected"] + stats["rows_clean"]
    ), "Row counts do not add up!"

    return kept, rejected, stats


def print_summary(stats: dict) -> None:
    print("CLEANING SUMMARY")
    print("=" * 46)
    print(f"{'Rows in':<32}{stats['rows_in']:>12,}")
    print(f"{'Duplicates removed':<32}{stats['duplicates_removed']:>12,}")
    print("Rejected (moved to rejected table):")
    for reason, n in stats["rejected_by_reason"].items():
        print(f"  {reason:<30}{n:>12,}")
    print(f"{'Total rejected':<32}{stats['rows_rejected']:>12,}")
    print(f"{'Clean rows kept':<32}{stats['rows_clean']:>12,}")


if __name__ == "__main__":
    clean_df, rejected_df, run_stats = clean(extract())
    print_summary(run_stats)