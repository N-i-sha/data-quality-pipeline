# Data Quality Report

- Run time: 2026-10-11 01:38:32
- Duration: 8.4 seconds
- Result: **PASS** (9 of 9 checks passed on the clean data)

## Row accounting

| Stage | Rows |
|---|---:|
| Rows in (raw) | 1,067,371 |
| Duplicates removed | 34,335 |
| Rejected (set aside with a reason) | 253,611 |
| &nbsp;&nbsp;- missing_customer_id | 228,488 |
| &nbsp;&nbsp;- cancelled_invoice | 19,104 |
| &nbsp;&nbsp;- non_positive_quantity | 3,393 |
| &nbsp;&nbsp;- non_positive_price | 2,626 |
| **Clean rows kept** | **779,425** |

## SQLite tables

| Table | Rows |
|---|---:|
| sales_clean | 779,425 |
| sales_rejected | 253,611 |

## Quality checks: before vs after cleaning

| Check | Bad rows in raw data | Bad rows in clean data | Status |
|---|---:|---:|---|
| has_expected_columns | 0 | 0 | PASS |
| no_duplicate_rows | 34,335 | 0 | PASS |
| no_missing_customer_id | 243,007 | 0 | PASS |
| no_missing_description | 4,382 | 0 | PASS |
| quantity_positive | 22,950 | 0 | PASS |
| price_positive | 6,207 | 0 | PASS |
| no_cancelled_invoices | 19,494 | 0 | PASS |
| valid_dates | 0 | 0 | PASS |
| no_future_dates | 0 | 0 | PASS |
