"""Phase 5: automated data quality tests.

Run from the project root:
    python -m pytest tests/ -v
"""
import sqlite3
from contextlib import closing

import pytest

from src.clean import clean
from src.extract import extract
from src.load import load
from src.quality_checks import CHECKS, with_standard_names

# Checks that MUST find problems in the raw data.
# If a check cannot fail on messy data, it is not really checking anything.
EXPECTED_TO_FAIL_ON_RAW = [
    "no_duplicate_rows",
    "no_missing_customer_id",
    "no_missing_description",
    "quantity_positive",
    "price_positive",
    "no_cancelled_invoices",
]

# Bad-row conditions we check directly in the SQLite database with SQL.
BAD_ROW_CONDITIONS = [
    "customer_id IS NULL",
    "quantity <= 0",
    "price <= 0",
    "invoice LIKE 'C%'",
]


@pytest.fixture(scope="session")
def raw_df():
    return extract()


@pytest.fixture(scope="session")
def cleaned(raw_df):
    return clean(raw_df)


@pytest.fixture(scope="session")
def database(cleaned, tmp_path_factory):
    clean_df, rejected_df, _ = cleaned
    db_path = tmp_path_factory.mktemp("db") / "test_retail.db"
    load(clean_df, rejected_df, db_path=db_path)
    return db_path


# ---------- 1. The clean data must pass every check ----------

@pytest.mark.parametrize("check_name", list(CHECKS))
def test_clean_data_passes(cleaned, check_name):
    clean_df, _, _ = cleaned
    bad_rows = CHECKS[check_name](clean_df)
    assert bad_rows == 0, f"{check_name} found {bad_rows} bad rows in the clean data"


# ---------- 2. The checks must catch problems in the raw data ----------

@pytest.mark.parametrize("check_name", EXPECTED_TO_FAIL_ON_RAW)
def test_checks_catch_problems_in_raw_data(raw_df, check_name):
    bad_rows = CHECKS[check_name](with_standard_names(raw_df))
    assert bad_rows > 0, f"{check_name} found nothing in the raw data, so it may be broken"


# ---------- 3. No row may disappear without a trace ----------

def test_every_row_is_accounted_for(raw_df, cleaned):
    _, _, stats = cleaned
    assert stats["rows_in"] == len(raw_df)
    total = stats["duplicates_removed"] + stats["rows_rejected"] + stats["rows_clean"]
    assert total == len(raw_df)


def test_every_rejected_row_has_a_reason(cleaned):
    _, rejected_df, _ = cleaned
    assert rejected_df["reject_reason"].notna().all()


# ---------- 4. The SQLite database must match and be clean ----------

def test_database_row_counts_match(cleaned, database):
    clean_df, rejected_df, _ = cleaned
    with closing(sqlite3.connect(database)) as conn:
        n_clean = conn.execute("SELECT COUNT(*) FROM sales_clean").fetchone()[0]
        n_rejected = conn.execute("SELECT COUNT(*) FROM sales_rejected").fetchone()[0]
    assert n_clean == len(clean_df)
    assert n_rejected == len(rejected_df)


@pytest.mark.parametrize("condition", BAD_ROW_CONDITIONS)
def test_database_has_no_bad_rows(database, condition):
    with closing(sqlite3.connect(database)) as conn:
        bad_rows = conn.execute(
            f"SELECT COUNT(*) FROM sales_clean WHERE {condition}"
        ).fetchone()[0]
    assert bad_rows == 0, f"{bad_rows} rows in sales_clean match: {condition}"