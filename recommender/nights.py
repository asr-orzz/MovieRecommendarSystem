"""Steer a taste query toward a watch-night mood and a discovery style.

Mood is a nudge, not a takeover: we slightly boost matching genre tokens
that already appear in the query, then add a small genre-overlap bonus so
Inception on a brainy night still stays near Nolan/sci-fi — not random
documentaries.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.preprocessing import normalize

NIGHT_PRESETS: dict[str, list[str]] = {
    "balanced": [],
    "intense": ["action", "thriller", "crime", "horror", "war"],
    "brainy": ["sciencefiction", "mystery", "drama", "documentary", "history"],
    "comfort": ["comedy", "romance", "family", "animation", "music"],
}

NIGHT_GENRES: dict[str, set[str]] = {
    "balanced": set(),
    "intense": {"Action", "Thriller", "Crime", "Horror", "War"},
    "brainy": {"Science Fiction", "Mystery", "Drama", "Documentary", "History"},
    "comfort": {"Comedy", "Romance", "Family", "Animation", "Music"},
}

NIGHT_LABELS = {
    "balanced": "Balanced",
    "intense": "Intense night",
    "brainy": "Brainy night",
    "comfort": "Comfort night",
}


def steer_query(
    query: np.ndarray,
    feature_names: np.ndarray | None,
    night: str = "balanced",
    strength: float = 0.12,
) -> np.ndarray:
    tokens = NIGHT_PRESETS.get(night, [])
    if query is None or feature_names is None or not tokens:
        return query

    steered = np.asarray(query, dtype=float).ravel().copy()
    names = np.asarray(feature_names)
    touched = False
    for token in tokens:
        hits = np.flatnonzero(names == token)
        if not len(hits):
            continue
        # Only amplify genres already in the blend so we do not invent a mood.
        if np.any(steered[hits] > 1e-9):
            steered[hits] += strength
            touched = True
    if not touched:
        return query
    return normalize(steered.reshape(1, -1), norm="l2")[0]


def apply_night_bonus(
    scores: np.ndarray,
    movies: pd.DataFrame,
    night: str = "balanced",
    strength: float = 0.045,
) -> np.ndarray:
    targets = NIGHT_GENRES.get(night) or set()
    adjusted = np.asarray(scores, dtype=float).copy()
    if not targets:
        return adjusted
    bonus = movies["genres"].apply(lambda genres: len(set(genres) & targets) * strength)
    valid = np.isfinite(adjusted)
    adjusted[valid] = adjusted[valid] + bonus.to_numpy(dtype=float)[valid]
    return adjusted


def apply_discovery(
    scores: np.ndarray,
    movies: pd.DataFrame,
    discovery: float = 0.0,
    strength: float = 0.12,
) -> np.ndarray:
    """discovery: -1 hidden gems, 0 balanced, +1 crowd-pleasers."""
    adjusted = np.asarray(scores, dtype=float).copy()
    if abs(discovery) < 1e-6:
        return adjusted

    valid = np.isfinite(adjusted)
    popularity = np.log1p(movies["popularity"].to_numpy(dtype=float))
    votes = np.log1p(movies["vote_count"].to_numpy(dtype=float))
    rating = movies["vote_average"].to_numpy(dtype=float) / 10.0
    fame = 0.5 * (
        popularity / (popularity.max() or 1.0) + votes / (votes.max() or 1.0)
    )
    shift = discovery * fame
    if discovery < 0:
        shift = shift + (-discovery) * rating * 0.5
    adjusted[valid] = adjusted[valid] + strength * shift[valid]
    return adjusted
