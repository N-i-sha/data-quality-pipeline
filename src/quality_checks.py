"""Data quality checks.

Every check returns the NUMBER OF BAD ROWS it finds.
0 means the check passed. Anything above 0 means it failed.

The same checks run on the raw data (where we EXPECT failures) and on the
cleaned data (where we expect everything to pass).
"""
import pandas as pd

from src.clean import COLUMN_NAMES

EXPECTED_COLUMNS = list(COLUMN_NAMES.values())


def with_standard_names(df: pd.DataFrame) -> pd.DataFrame:
    """Give raw columns the same names as the clean table (names only, no cleaning)."""
    return df.rename(columns=COLUMN_NAMES)


def has_expected_columns(df: pd.DataFrame) -> int:
    return len(set(EXPECTED_COLUMNS) - set(df.columns))


def no_duplicate_rows(df: pd.DataFrame) -> int:
    return int(df.duplicated().sum())


def no_missing_customer_id(df: pd.DataFrame) -> int:
    return int(df["customer_id"].isna().sum())


def no_missing_description(df: pd.DataFrame) -> int:
    return int(df["description"].isna().sum())


def quantity_positive(df: pd.DataFrame) -> int:
    quantity = pd.to_numeric(df["quantity"], errors="coerce")
    return int((~(quantity > 0)).sum())


def price_positive(df: pd.DataFrame) -> int:
    price = pd.to_numeric(df["price"], errors="coerce")
    return int((~(price > 0)).sum())


def no_cancelled_invoices(df: pd.DataFrame) -> int:
    return int(df["invoice"].astype(str).str.startswith("C").sum())


def valid_dates(df: pd.DataFrame) -> int:
    return int(pd.to_datetime(df["invoice_date"], errors="coerce").isna().sum())


def no_future_dates(df: pd.DataFrame) -> int:
    dates = pd.to_datetime(df["invoice_date"], errors="coerce")
    return int((dates > pd.Timestamp.now()).sum())


CHECKS = {
    check.__name__: check
    for check in [
        has_expected_columns,
        no_duplicate_rows,
        no_missing_customer_id,
        no_missing_description,
        quantity_positive,
        price_positive,
        no_cancelled_invoices,
        valid_dates,
        no_future_dates,
    ]
}


def run_checks(df: pd.DataFrame) -> list:
    """Run every check and return a list of results (used by the report in Phase 6)."""
    results = []
    for name, check in CHECKS.items():
        bad_rows = check(df)
        results.append({"check": name, "bad_rows": bad_rows, "passed": bad_rows == 0})
    return results