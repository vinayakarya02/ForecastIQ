"""Forecasting layer: build series -> fit candidate models -> evaluate -> select best.

Models share a common fit/forecast interface (models.py) so new models are drop-in.
Orchestrated by ``pipelines/run_forecast.py``. (Implementations land in Phase 3.)
"""
