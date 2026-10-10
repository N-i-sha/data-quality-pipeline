"""Runs extract -> clean -> load -> quality checks -> report in one command.
(Built in Phase 6.)
"""
"""Runs the whole pipeline with ONE command:

    extract -> clean -> load -> quality checks -> report

Run from the project root:
    python -m src.run_pipeline

Exit code 0 means every check passed on the clean data.
Exit code 1 means something failed (this is what turns CI red).
"""
import sys
import time
from datetime import datetime
from pathlib import Path

from src.clean import clean
from src.extract import extract
from src.load import load
from src.quality_checks import run_checks, with_standard_names

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORT_PATH = PROJECT_ROOT / "reports" / "quality_report.md"


def build_report(stats, raw_results, clean_results, db_counts, seconds) -> str:
    """Turn the numbers into a readable Markdown report."""
    all_passed = all(r["passed"] for r in clean_results)
    verdict = "PASS" if all_passed else "FAIL"
    raw_by_name = {r["check"]: r["bad_rows"] for r in raw_results}

    lines = [
        "# Data Quality Report",
        "",
        f"- Run time: {datetime.now():%Y-%m-%d %H:%M:%S}",
        f"- Duration: {seconds:.1f} seconds",
        f"- Result: **{verdict}** ({sum(r['passed'] for r in clean_results)} of "
        f"{len(clean_results)} checks passed on the clean data)",
        "",
        "## Row accounting",
        "",
        "| Stage | Rows |",
        "|---|---:|",
        f"| Rows in (raw) | {stats['rows_in']:,} |",
        f"| Duplicates removed | {stats['duplicates_removed']:,} |",
        f"| Rejected (set aside with a reason) | {stats['rows_rejected']:,} |",
    ]
    for reason, n in stats["rejected_by_reason"].items():
        lines.append(f"| &nbsp;&nbsp;- {reason} | {n:,} |")
    lines += [
        f"| **Clean rows kept** | **{stats['rows_clean']:,}** |",
        "",
        "## SQLite tables",
        "",
        "| Table | Rows |",
        "|---|---:|",
    ]
    for table, n in db_counts.items():
        lines.append(f"| {table} | {n:,} |")
    lines += [
        "",
        "## Quality checks: before vs after cleaning",
        "",
        "| Check | Bad rows in raw data | Bad rows in clean data | Status |",
        "|---|---:|---:|---|",
    ]
    for r in clean_results:
        status = "PASS" if r["passed"] else "FAIL"
        lines.append(
            f"| {r['check']} | {raw_by_name[r['check']]:,} | {r['bad_rows']:,} | {status} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    start = time.time()

    raw_df = extract()
    clean_df, rejected_df, stats = clean(raw_df)
    db_counts = load(clean_df, rejected_df)

    raw_results = run_checks(with_standard_names(raw_df))
    clean_results = run_checks(clean_df)

    report = build_report(stats, raw_results, clean_results, db_counts, time.time() - start)
    REPORT_PATH.write_text(report, encoding="utf-8")

    print(report)
    print(f"Report saved to: {REPORT_PATH}")

    return 0 if all(r["passed"] for r in clean_results) else 1


if __name__ == "__main__":
    sys.exit(main())