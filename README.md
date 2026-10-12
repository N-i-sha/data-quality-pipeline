# Data Pipeline with Automated Data Quality Testing

[![Data Quality Pipeline](https://github.com/N-i-sha/data-quality-pipeline/actions/workflows/tests.yml/badge.svg)](https://github.com/N-i-sha/data-quality-pipeline/actions)

A small data pipeline that reads a messy retail dataset (1M+ rows), cleans it,
loads it into SQLite, and **proves the data is clean** with automated tests
that run on every push.

## Why this project

Reports and dashboards are only as trustworthy as the data under them. In my
churn analysis project I cleaned data by hand and trusted the result. Here I
automated both the cleaning and the verification, so bad data is caught by
tests instead of by luck.

The structure (extract, clean, load, test, report) is reusable. For a new
dataset, the column names, cleaning rules and checks would be rewritten.

## What it does

```
raw CSV -> profile -> clean -> SQLite (sales_clean + sales_rejected)
                                 |
                  quality checks + 22 Pytest tests
                                 |
                   reports/quality_report.md  ->  GitHub Actions: pass / fail
```

## Results on the full dataset

Dataset: Online Retail II, transactions from a UK online retailer (Dec 2009 to Dec 2011).

| Stage                   |      Rows |
| ----------------------- | --------: |
| Rows in (raw)           | 1,067,371 |
| Duplicates removed      |    34,335 |
| Rejected, with a reason |   253,611 |
| Clean rows kept         |   779,425 |

Bad rows found by each check, before and after cleaning:

| Check                                              | Raw data | Clean data |
| -------------------------------------------------- | -------: | ---------: |
| no_duplicate_rows                                  |   34,335 |          0 |
| no_missing_customer_id                             |  243,007 |          0 |
| no_missing_description                             |    4,382 |          0 |
| quantity_positive                                  |   22,950 |          0 |
| price_positive                                     |    6,207 |          0 |
| no_cancelled_invoices                              |   19,494 |          0 |
| has_expected_columns, valid_dates, no_future_dates |        0 |          0 |

The full report is in [`reports/quality_report.md`](reports/quality_report.md).
The pipeline runs end to end in under 10 seconds.

## Cleaning rules

| Rule                                       | Why                                                   |
| ------------------------------------------ | ----------------------------------------------------- |
| Drop exact duplicate rows                  | The same line counted twice inflates revenue          |
| Reject cancelled invoices (start with "C") | Returns are not sales                                 |
| Reject quantity <= 0 or price <= 0         | Not valid sales                                       |
| Reject rows with no customer ID            | Customer-level analysis such as RFM needs one         |
| Reject invalid dates                       | A sale needs a valid date                             |
| Fill missing descriptions with "UNKNOWN"   | The sale itself is valid, so it is fixed, not removed |

Rejected rows are **not deleted**. They go to a `sales_rejected` table with a
`reject_reason` column. Each row gets only its first matching reason, so the
reasons add up exactly to the total.

## Tests

22 Pytest tests in four groups:

1. **Clean data passes all 9 checks** (9 tests)
2. **The checks catch problems in the raw data** (6 tests). A check that can
   never fail proves nothing, so the same checks must find problems in the raw data.
3. **Every row is accounted for** (2 tests): rows in = duplicates + rejected + clean,
   and every rejected row has a reason.
4. **The SQLite database matches and is clean** (5 tests), checked with SQL.

## How to run

```bash
pip install -r requirements.txt

# Download the Online Retail II CSV and place it at:
#   data/raw/online_retail_II.csv

python -m src.run_pipeline        # runs everything and writes the report
python -m pytest tests/ -v        # runs the 22 tests
```

The full CSV is too large for GitHub, so it is not in this repo. On GitHub
Actions the pipeline uses `data/sample/`, a small sample built by
`src/make_sample.py`. The sample is built on purpose to contain every problem
type, because a purely random sample would almost never include both copies of
a duplicate pair.

## Project structure

```
src/
  extract.py          read the raw CSV (uses the sample if the full file is missing)
  profile_data.py     count the problems before cleaning
  clean.py            apply the rules, split clean and rejected rows
  load.py             write both tables to SQLite and verify the counts
  quality_checks.py   the 9 data quality checks
  make_sample.py      build the small sample used by CI
  run_pipeline.py     run every step and write the report
tests/
  test_data_quality.py
reports/
  quality_report.md
.github/workflows/tests.yml
```

## Design decisions

- **Reject, don't delete:** nothing disappears without a recorded reason.
- **Safety checks inside the code:** assertions confirm that row counts add up
  after cleaning and after loading.
- **Exit code:** the pipeline exits with an error if a check fails on the clean
  data, so CI turns red.

## Limitations and next steps

- The rules and checks are written for this dataset's columns.
- About 21% of rows were rejected for a missing customer ID. This is a
  judgment call that suits customer-level analysis, and those rows are kept in
  the rejected table so they can be reused.
- Next steps: read rules from a config file, try Great Expectations for the
  checks, and move from SQLite to PostgreSQL for larger data.
