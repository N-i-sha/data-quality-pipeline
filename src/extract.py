"""EXTRACT step: read the raw CSV into a pandas DataFrame.
(Built in Phase 2.)
"""
"""EXTRACT step: read the raw CSV into a pandas DataFrame.

The raw file is never modified. We only read it.
"""
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "online_retail_II.csv"


def extract(path=RAW_PATH) -> pd.DataFrame:
    """Read the raw CSV and return it untouched."""
    try:
        return pd.read_csv(path)
    except UnicodeDecodeError:
        # Some copies of this dataset are not UTF-8. latin-1 can read any bytes.
        return pd.read_csv(path, encoding="latin-1")