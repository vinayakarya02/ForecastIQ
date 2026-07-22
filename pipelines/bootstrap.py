"""Build the warehouse if it's missing.

Uses the real dataset when present, otherwise generates synthetic sample data — so a
fresh environment (container, cloud) comes up as a working demo with no manual steps.

Usage:
    python pipelines/bootstrap.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from forecastiq.bootstrap import ensure_warehouse  # noqa: E402


def main() -> int:
    mode = ensure_warehouse()
    print(f"Warehouse ready ({mode} data).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
