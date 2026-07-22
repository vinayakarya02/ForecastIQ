"""ForecastIQ ETL entrypoint: raw CSV -> validated star-schema warehouse.

Usage:
    python pipelines/run_etl.py
    python pipelines/run_etl.py --config config/config.yaml
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Make `import forecastiq` work when running this script directly (no install needed).
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from forecastiq.bootstrap import record_data_mode  # noqa: E402
from forecastiq.config import Config  # noqa: E402
from forecastiq.etl.clean import clean  # noqa: E402
from forecastiq.etl.extract import extract  # noqa: E402
from forecastiq.etl.load import load, write_quality_log  # noqa: E402
from forecastiq.etl.transform import transform  # noqa: E402
from forecastiq.etl.validate import validate  # noqa: E402
from forecastiq.utils.logger import get_logger  # noqa: E402


def _print_report(report) -> None:
    try:
        from tabulate import tabulate

        print(tabulate(report, headers="keys", tablefmt="github", showindex=False))
    except ImportError:  # tabulate is optional at runtime
        print(report.to_string(index=False))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the ForecastIQ ETL pipeline.")
    parser.add_argument("--config", default=None, help="Path to config.yaml")
    args = parser.parse_args()

    cfg = Config.load(args.config)
    logger = get_logger()
    run_id = datetime.now().strftime("etl_%Y%m%d_%H%M%S")
    logger.info("=== ForecastIQ ETL  (run_id=%s) ===", run_id)

    # Extract -> Clean -> Validate
    raw = extract(cfg, logger)
    cleaned = clean(raw, cfg, logger)
    report, ok = validate(cleaned, cfg, logger)

    print("\nData-quality report")
    print("-------------------")
    _print_report(report)
    print()

    if not ok:
        logger.error("Validation FAILED — aborting before load. Fix the source data or thresholds.")
        return 1

    # Transform -> Load
    tables = transform(cleaned, cfg, logger)
    summary = load(tables, cfg, logger)
    write_quality_log(report, cfg, run_id)
    record_data_mode(cfg, "real", cfg.source_path.name)

    total = sum(summary.values())
    logger.info("=== ETL complete: %d rows across %d tables ===", total, len(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
