"""Build a structured TMDB catalog and L2-normalized bag-of-words matrix.

The original notebook mashed genres, cast, crew, and overview into a single
`tags` string, then threw the structured fields away. That is enough for
"pick one movie, get five similar titles", but it cannot explain a pick or
blend several movies. This pipeline keeps both:

- readable metadata (genres, top cast, directors, keywords, ratings)
- a CountVectorizer matrix with L2-normalized rows so cosine similarity
  is a dot product, and movie vectors can be averaged like embeddings
"""

from __future__ import annotations

import ast
import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.preprocessing import normalize

ARTIFACT_DIR = Path("artifacts")
CATALOG_PATH = ARTIFACT_DIR / "catalog.pkl"

DATA_DIR = Path(".")
MOVIES_CSV = DATA_DIR / "tmdb_5000_movies.csv"
CREDITS_CSV = DATA_DIR / "tmdb_5000_credits.csv"

MOVIE_MIRRORS = [
    "https://raw.githubusercontent.com/PinkWink/ML_tutorial/master/dataset/tmdb_5000_movies.csv",
]
CREDIT_MIRRORS = [
    "https://github.com/harshitcodes/tmdb_movie_data_analysis/raw/master/tmdb-5000-movie-dataset/tmdb_5000_credits.csv",
    "https://media.githubusercontent.com/media/harshitcodes/tmdb_movie_data_analysis/master/tmdb-5000-movie-dataset/tmdb_5000_credits.csv",
]


def _parse_name_list(raw: Any) -> list[str]:
    if raw is None or (isinstance(raw, float) and np.isnan(raw)):
        return []
    if isinstance(raw, list):
        return [str(item) for item in raw]
    try:
        parsed = ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        return []
    names: list[str] = []
    for item in parsed:
        if isinstance(item, dict) and item.get("name"):
            names.append(str(item["name"]))
    return names


def _parse_directors(raw: Any) -> list[str]:
    if raw is None or (isinstance(raw, float) and np.isnan(raw)):
        return []
    try:
        parsed = ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        return []
    return [
        str(item["name"])
        for item in parsed
        if isinstance(item, dict) and item.get("job") == "Director" and item.get("name")
    ]


def _collapse(names: list[str]) -> list[str]:
    """Remove spaces so 'Sam Worthington' is one token, not two."""
    return [name.replace(" ", "") for name in names if name]


def _download(url: str, dest: Path) -> None:
    import requests

    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()
        with dest.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 256):
                if chunk:
                    handle.write(chunk)


def ensure_tmdb_csvs(movies_path: Path = MOVIES_CSV, credits_path: Path = CREDITS_CSV) -> None:
    """Use local TMDB CSVs when present; otherwise fetch public mirrors."""
    if not movies_path.exists():
        last_error: Exception | None = None
        for url in MOVIE_MIRRORS:
            try:
                _download(url, movies_path)
                break
            except Exception as exc:  # noqa: BLE001 — try the next mirror
                last_error = exc
        else:
            raise FileNotFoundError(
                f"Could not download {movies_path.name}. Last error: {last_error}"
            )

    if not credits_path.exists():
        last_error = None
        for url in CREDIT_MIRRORS:
            try:
                _download(url, credits_path)
                if credits_path.stat().st_size > 1_000_000:
                    break
                credits_path.unlink(missing_ok=True)
            except Exception as exc:  # noqa: BLE001 — try the next mirror
                last_error = exc
                credits_path.unlink(missing_ok=True)
        else:
            raise FileNotFoundError(
                f"Could not download {credits_path.name}. Last error: {last_error}"
            )


def build_catalog(
    movies_path: Path = MOVIES_CSV,
    credits_path: Path = CREDITS_CSV,
    max_features: int = 5000,
) -> dict[str, Any]:
    """Return a catalog dict ready to pickle: movies frame + normalized matrix."""
    movies = pd.read_csv(movies_path)
    credits = pd.read_csv(credits_path)

    frame = movies.merge(credits, left_on="id", right_on="movie_id", suffixes=("", "_cred"))
    frame["overview"] = frame["overview"].fillna("")
    frame["release_date"] = pd.to_datetime(frame["release_date"], errors="coerce")

    readable_genres = frame["genres"].apply(_parse_name_list)
    readable_keywords = frame["keywords"].apply(_parse_name_list)
    readable_cast = frame["cast"].apply(lambda raw: _parse_name_list(raw)[:3])
    readable_directors = frame["crew"].apply(_parse_directors)

    overview_tokens = frame["overview"].apply(lambda text: str(text).split())
    tags = (
        overview_tokens
        + readable_genres.apply(_collapse)
        + readable_keywords.apply(_collapse)
        + readable_cast.apply(_collapse)
        + readable_directors.apply(_collapse)
    ).apply(lambda tokens: " ".join(tokens))

    catalog_movies = pd.DataFrame(
        {
            "movie_id": frame["id"].astype(int),
            "title": frame["title"],
            "overview": frame["overview"],
            "genres": readable_genres,
            "cast": readable_cast,
            "directors": readable_directors,
            "keywords": readable_keywords,
            "tags": tags,
            "vote_average": frame["vote_average"].fillna(0.0).astype(float),
            "vote_count": frame["vote_count"].fillna(0).astype(int),
            "popularity": frame["popularity"].fillna(0.0).astype(float),
            "release_year": frame["release_date"].dt.year.fillna(0).astype(int),
        }
    )
    catalog_movies = catalog_movies.drop_duplicates(subset=["movie_id"]).reset_index(drop=True)

    vectorizer = CountVectorizer(max_features=max_features, stop_words="english")
    raw_matrix = vectorizer.fit_transform(catalog_movies["tags"])
    matrix = normalize(raw_matrix, norm="l2", copy=False)

    return {
        "movies": catalog_movies,
        "matrix": matrix,
        "vectorizer": vectorizer,
        "feature_names": np.array(vectorizer.get_feature_names_out()),
    }


def save_catalog(catalog: dict[str, Any], path: Path = CATALOG_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "movies": catalog["movies"],
        "matrix": sparse.csr_matrix(catalog["matrix"]),
        "vectorizer": catalog["vectorizer"],
        "feature_names": catalog["feature_names"],
    }
    with path.open("wb") as handle:
        pickle.dump(payload, handle, protocol=pickle.HIGHEST_PROTOCOL)
    return path


def load_catalog(path: Path = CATALOG_PATH) -> dict[str, Any]:
    with path.open("rb") as handle:
        catalog = pickle.load(handle)
    catalog["matrix"] = sparse.csr_matrix(catalog["matrix"])
    return catalog
