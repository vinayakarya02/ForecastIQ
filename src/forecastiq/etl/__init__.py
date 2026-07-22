"""ETL layer: extract -> clean -> validate -> transform -> load.

Each stage lives in its own module and exposes a small, testable function.
Orchestrated by ``pipelines/run_etl.py``.
"""
