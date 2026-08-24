"""Download TMDB CSVs into data/raw and build artifacts/catalog.pkl."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from recommender.paths import CATALOG_PATH
from recommender.pipeline import build_catalog, ensure_tmdb_csvs, save_catalog


def main() -> None:
    print("Checking TMDB source files in data/raw ...")
    ensure_tmdb_csvs()
    print("Building structured catalog and feature matrix...")
    catalog = build_catalog()
    path = save_catalog(catalog)
    n_movies, n_features = catalog["matrix"].shape
    print(f"Saved {n_movies} movies x {n_features} features to {path}")
    print(f"(also available as {CATALOG_PATH})")


if __name__ == "__main__":
    main()
