"""EXTRACT step: read the raw CSV into a pandas DataFrame.

The raw file is never modified. We only read it.

On your laptop the full file in data/raw/ is used. On GitHub Actions the big
file does not exist, so the small sample in data/sample/ is used instead.
You can also force the sample locally by setting the USE_SAMPLE=1 variable.
"""
import os
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "online_retail_II.csv"
SAMPLE_PATH = PROJECT_ROOT / "data" / "sample" / "online_retail_II_sample.csv"


def default_path() -> Path:
    """Use the sample when forced, or when the full raw file is not there."""
    if os.environ.get("USE_SAMPLE") == "1" or not RAW_PATH.exists():
        return SAMPLE_PATH
    return RAW_PATH


def extract(path=None) -> pd.DataFrame:
    """Read the CSV and return it untouched."""
    path = path or default_path()
    try:
        return pd.read_csv(path)
    except UnicodeDecodeError:
        # Some copies of this dataset are not UTF-8. latin-1 can read any bytes.
        return pd.read_csv(path, encoding="latin-1")