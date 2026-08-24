"""Project-root paths so scripts work from any working directory."""

from __future__ import annotations

import os
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent

DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
ARTIFACT_DIR = PROJECT_ROOT / "artifacts"

MOVIES_CSV = DATA_RAW_DIR / "tmdb_5000_movies.csv"
CREDITS_CSV = DATA_RAW_DIR / "tmdb_5000_credits.csv"
CATALOG_PATH = ARTIFACT_DIR / "catalog.pkl"
ENV_PATH = PROJECT_ROOT / ".env"


def load_env(path: Path = ENV_PATH) -> None:
    """Load KEY=VALUE pairs from .env without adding a dependency."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
