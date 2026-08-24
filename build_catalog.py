"""Download TMDB CSVs if needed and build artifacts/catalog.pkl."""

from recommender.pipeline import (
    CATALOG_PATH,
    build_catalog,
    ensure_tmdb_csvs,
    save_catalog,
)


def main() -> None:
    print("Checking TMDB source files...")
    ensure_tmdb_csvs()
    print("Building structured catalog and feature matrix...")
    catalog = build_catalog()
    path = save_catalog(catalog)
    n_movies, n_features = catalog["matrix"].shape
    print(f"Saved {n_movies} movies x {n_features} features to {path}")


if __name__ == "__main__":
    main()
