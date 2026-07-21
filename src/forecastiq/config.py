"""Configuration loader.

Loads ``config/config.yaml`` and layers environment-variable overrides on top,
so code never hard-codes paths, model params, or the database URL.
"""
from __future__ import annotations

import os
from pathlib import Path

import yaml

# .../ForecastIQ  (two levels up from src/forecastiq/config.py)
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Config:
    """Thin, dict-backed accessor over the YAML config with env overrides."""

    def __init__(self, data: dict):
        self._data = data

    @classmethod
    def load(cls, path: str | Path | None = None) -> "Config":
        cfg_path = Path(path) if path else PROJECT_ROOT / "config" / "config.yaml"
        with open(cfg_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(data)

    # -- dict-style access -------------------------------------------------
    def __getitem__(self, key):
        return self._data[key]

    def get(self, key, default=None):
        return self._data.get(key, default)

    # -- resolved conveniences --------------------------------------------
    @property
    def root(self) -> Path:
        return PROJECT_ROOT

    @property
    def db_url(self) -> str:
        """DB URL from env or config; relative SQLite paths are anchored to project root."""
        url = os.getenv("FORECASTIQ_DB_URL") or self._data["database"]["url"]
        prefix = "sqlite:///"
        if url.startswith(prefix) and not url.startswith("sqlite:////"):
            rel = url[len(prefix):]
            url = prefix + (PROJECT_ROOT / rel).as_posix()
        return url

    @property
    def raw_csv(self) -> Path:
        rel = os.getenv("FORECASTIQ_RAW_CSV") or self._data["paths"]["raw_csv"]
        return self._resolve(rel)

    def path(self, *keys) -> Path:
        """Resolve a nested path value from config to an absolute Path."""
        node = self._data
        for k in keys:
            node = node[k]
        return self._resolve(node)

    @staticmethod
    def _resolve(rel: str | Path) -> Path:
        p = Path(rel)
        return p if p.is_absolute() else (PROJECT_ROOT / p)
