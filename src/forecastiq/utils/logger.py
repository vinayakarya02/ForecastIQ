"""Configured logging — a single, consistent logger across the platform."""
from __future__ import annotations

import logging
import os

_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
_DATEFMT = "%H:%M:%S"


def get_logger(name: str = "forecastiq", level: str | None = None) -> logging.Logger:
    """Return a module logger with a single stream handler (idempotent)."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(_FORMAT, _DATEFMT))
        logger.addHandler(handler)
        logger.propagate = False
    logger.setLevel(level or os.getenv("FORECASTIQ_LOG_LEVEL", "INFO"))
    return logger
