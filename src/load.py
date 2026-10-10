"""LOAD step: save the cleaned data into a SQLite database.
(Built in Phase 4.)
"""
"""LOAD step: save the cleaned data into a SQLite database.

Two tables are created:
    sales_clean     the trusted rows
    sales_rejected  the rows we set aside, with a reject_reason column

Run from the project root:
    python -m src.load
"""
import sqlite3
from contextlib import closing
from pathlib import Path

import pandas as pd

from src.clean import clean
from src.extract import extract

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "retail.db"


def load(clean_df: pd.DataFrame, rejected_df: pd.DataFrame, db_path=DB_PATH) -> dict:
    """Write both tables to SQLite and return the row counts found in the database."""
    with closing(sqlite3.connect(db_path)) as conn:
        # if_exists="replace" makes the pipeline safe to run again and again.
        clean_df.to_sql("sales_clean", conn, if_exists="replace", index=False, chunksize=50_000)
        rejected_df.to_sql("sales_rejected", conn, if_exists="replace", index=False, chunksize=50_000)
        conn.commit()

        counts = {
            table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("sales_clean", "sales_rejected")
        }

    # Safety check: nothing was lost on the way into the database.
    assert counts["sales_clean"] == len(clean_df), "sales_clean row count mismatch!"
    assert counts["sales_rejected"] == len(rejected_df), "sales_rejected row count mismatch!"
    return counts


def top_countries(db_path=DB_PATH, n: int = 5) -> list:
    """A real SQL question on the clean table: which countries earn the most?"""
    query = """
        SELECT country, ROUND(SUM(quantity * price), 2) AS revenue
        FROM sales_clean
        GROUP BY country
        ORDER BY revenue DESC
        LIMIT ?
    """
    with closing(sqlite3.connect(db_path)) as conn:
        return conn.execute(query, (n,)).fetchall()


if __name__ == "__main__":
    clean_df, rejected_df, _ = clean(extract())
    counts = load(clean_df, rejected_df)
    print("LOADED INTO SQLITE")
    print("=" * 46)
    for table, n in counts.items():
        print(f"{table:<20}{n:>12,} rows")
    print()
    print("Top countries by revenue (from SQL):")
    for country, revenue in top_countries():
        print(f"  {country:<22}{revenue:>14,.2f}")