"""ETL layer: extract -> clean -> validate -> transform -> load.

Each stage is implemented in its own module and exposes a small, testable function.
Orchestrated by ``pipelines/run_etl.py``. (Implementations land in Phase 1.)
"""
