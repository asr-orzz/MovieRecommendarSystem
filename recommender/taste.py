"""Blend several movie vectors into one taste query.

Liked movies are averaged (like a user embedding). An optional skip list is
subtracted so `Avatar + Inception - The Notebook` steers away from romance
and toward cerebral sci-fi. Rows in the catalog matrix are already
L2-normalized, so cosine similarity is a dot product.
"""

from __future__ import annotations

from typing import Any, Iterable

import numpy as np
import pandas as pd
from sklearn.preprocessing import normalize


class UnknownMovieError(ValueError):
    pass


def movie_index(movies: pd.DataFrame, title: str) -> int:
    hits = movies.index[movies["title"] == title]
    if len(hits) == 0:
        raise UnknownMovieError(f"Unknown movie: {title}")
    return int(hits[0])


def movie_indices(movies: pd.DataFrame, titles: Iterable[str]) -> list[int]:
    return [movie_index(movies, title) for title in titles]


def blend_vectors(
    matrix,
    liked_indices: list[int],
    skipped_indices: list[int] | None = None,
    skip_weight: float = 0.45,
) -> np.ndarray:
    if not liked_indices:
        raise ValueError("Pick at least one movie you like.")

    liked = np.asarray(matrix[liked_indices].mean(axis=0)).ravel()
    if skipped_indices:
        skipped = np.asarray(matrix[skipped_indices].mean(axis=0)).ravel()
        liked = liked - float(skip_weight) * skipped
    return normalize(liked.reshape(1, -1), norm="l2")[0]


def score_catalog(
    matrix,
    query: np.ndarray,
    exclude: set[int] | None = None,
) -> np.ndarray:
    scores = np.asarray(matrix @ query).ravel()
    if exclude:
        scores[list(exclude)] = -np.inf
    return scores


def top_indices(scores: np.ndarray, top_n: int = 5) -> list[tuple[int, float]]:
    valid = np.isfinite(scores)
    if not valid.any():
        return []
    k = min(top_n, int(valid.sum()))
    candidates = np.argpartition(scores, -k)[-k:]
    ranked = candidates[np.argsort(scores[candidates])[::-1]]
    return [(int(i), float(scores[i])) for i in ranked]


def recommend_blend(
    catalog: dict[str, Any],
    liked_titles: list[str],
    skipped_titles: list[str] | None = None,
    top_n: int = 5,
    skip_weight: float = 0.45,
) -> list[dict[str, Any]]:
    movies = catalog["movies"]
    matrix = catalog["matrix"]
    liked_idx = movie_indices(movies, liked_titles)
    skipped_idx = movie_indices(movies, skipped_titles or [])
    query = blend_vectors(matrix, liked_idx, skipped_idx, skip_weight)
    scores = score_catalog(matrix, query, set(liked_idx) | set(skipped_idx))

    results: list[dict[str, Any]] = []
    for idx, score in top_indices(scores, top_n):
        row = movies.iloc[idx]
        results.append(
            {
                "index": idx,
                "movie_id": int(row["movie_id"]),
                "title": row["title"],
                "score": score,
                "genres": list(row["genres"]),
                "cast": list(row["cast"]),
                "directors": list(row["directors"]),
                "keywords": list(row["keywords"]),
                "overview": row["overview"],
                "vote_average": float(row["vote_average"]),
                "popularity": float(row["popularity"]),
                "release_year": int(row["release_year"]),
            }
        )
    return results
