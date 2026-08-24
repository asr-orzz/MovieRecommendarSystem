"""Project-root paths so scripts work from any working directory."""

from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent

DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
ARTIFACT_DIR = PROJECT_ROOT / "artifacts"

MOVIES_CSV = DATA_RAW_DIR / "tmdb_5000_movies.csv"
CREDITS_CSV = DATA_RAW_DIR / "tmdb_5000_credits.csv"
CATALOG_PATH = ARTIFACT_DIR / "catalog.pkl"
