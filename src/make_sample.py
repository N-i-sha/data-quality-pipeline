"""Create a small, deliberately messy sample of the raw data for GitHub Actions.

A purely random sample would almost never contain both copies of a duplicate
pair, so we build the sample on purpose: an ordinary slice of the file PLUS a
guaranteed handful of every problem type.

Run once from the project root:
    python -m src.make_sample
"""
import pandas as pd

from src.extract import RAW_PATH, SAMPLE_PATH, extract
from src.profile_data import profile

HEAD_ROWS = 3000      # an ordinary slice from the start of the file
PER_PROBLEM = 150     # rows picked for each problem type
SEED = 42             # makes the random picks repeatable


def build_sample(df: pd.DataFrame) -> pd.DataFrame:
    invoice = df["Invoice"].astype(str)
    quantity = pd.to_numeric(df["Quantity"], errors="coerce")
    price = pd.to_numeric(df["Price"], errors="coerce")
    cancelled = invoice.str.startswith("C")

    def pick(rows: pd.DataFrame, n: int) -> pd.DataFrame:
        return rows.sample(min(n, len(rows)), random_state=SEED)

    parts = [
        df.head(HEAD_ROWS),
        # tail() of the duplicated rows keeps both copies of each pair together
        df[df.duplicated(keep=False)].tail(2 * PER_PROBLEM),
        pick(df[df["Customer ID"].isna()], PER_PROBLEM),
        pick(df[cancelled], PER_PROBLEM),
        pick(df[(quantity <= 0) & ~cancelled], PER_PROBLEM),
        pick(df[~(price > 0)], PER_PROBLEM),
        pick(df[df["Description"].isna()], PER_PROBLEM),
    ]
    sample = pd.concat(parts)
    # A row picked by two groups must appear only once (this is by row position,
    # so genuine duplicate rows are NOT removed).
    return sample[~sample.index.duplicated()].sort_index()


if __name__ == "__main__":
    sample = build_sample(extract(RAW_PATH))
    SAMPLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    sample.to_csv(SAMPLE_PATH, index=False)

    found = profile(sample)
    print(f"Sample saved to: {SAMPLE_PATH}")
    print(f"Rows in sample: {len(sample):,}")
    print("Problems included:")
    for key in ["duplicate_rows", "missing_customer_id", "missing_description",
                "quantity_below_zero", "price_equal_zero", "cancelled_invoices"]:
        print(f"  {key:<24}{found[key]:>6,}")