"""Turn a blend hit into a readable 'because' card.

Most campus recommenders stop at a cosine score. This module walks the
structured metadata we kept in the catalog and reports the overlapping
DNA: shared directors, cast, genres, and plot keywords, plus which liked
movie the pick is closest to.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable

import numpy as np
import pandas as pd

FIELD_WEIGHTS = {
    "directors": 3.0,
    "cast": 2.5,
    "genres": 1.5,
    "keywords": 1.0,
}

FIELD_ORDER = ("directors", "cast", "genres", "keywords")


def _as_list(value: Any) -> list[str]:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return []
    if isinstance(value, str):
        return [value] if value else []
    return [str(item) for item in list(value) if item]


def _overlap(left: Iterable[str], right: Iterable[str]) -> list[str]:
    right_set = {item.casefold(): item for item in _as_list(right)}
    seen: set[str] = set()
    hits: list[str] = []
    for item in _as_list(left):
        key = item.casefold()
        if key in right_set and key not in seen:
            seen.add(key)
            hits.append(right_set[key])
    return hits


def _jaccard(left: Iterable[str], right: Iterable[str]) -> float:
    left_set = {item.casefold() for item in _as_list(left)}
    right_set = {item.casefold() for item in _as_list(right)}
    if not left_set and not right_set:
        return 0.0
    return len(left_set & right_set) / len(left_set | right_set)


def _seed_rows(movies: pd.DataFrame, titles: list[str]) -> tuple[list[int], list[dict[str, Any]]]:
    indices: list[int] = []
    rows: list[dict[str, Any]] = []
    for title in titles:
        hits = movies.index[movies["title"] == title]
        if len(hits) == 0:
            continue
        idx = int(hits[0])
        row = movies.iloc[idx]
        indices.append(idx)
        rows.append(
            {
                "index": idx,
                "title": row["title"],
                "genres": _as_list(row["genres"]),
                "cast": _as_list(row["cast"]),
                "directors": _as_list(row["directors"]),
                "keywords": _as_list(row["keywords"]),
            }
        )
    return indices, rows


def _cosine_pair(matrix, left: int, right: int) -> float:
    value = matrix[left] @ matrix[right].T
    if hasattr(value, "toarray"):
        return float(value.toarray()[0, 0])
    return float(np.asarray(value).ravel()[0])


def closest_seed(
    matrix,
    rec_index: int,
    seed_indices: list[int],
    seed_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    if not seed_indices:
        return {"title": "", "score": 0.0, "index": -1}
    best_i = 0
    best_score = -1.0
    for i, seed_index in enumerate(seed_indices):
        score = _cosine_pair(matrix, rec_index, seed_index)
        if score > best_score:
            best_i = i
            best_score = score
    return {
        "title": seed_rows[best_i]["title"],
        "score": best_score,
        "index": seed_indices[best_i],
    }


def _field_overlaps(rec: dict[str, Any], seeds: list[dict[str, Any]]) -> dict[str, list[str]]:
    overlaps: dict[str, list[str]] = {}
    for field in FIELD_ORDER:
        hits: list[str] = []
        seen: set[str] = set()
        rec_values = _as_list(rec.get(field))
        for seed in seeds:
            for item in _overlap(rec_values, seed.get(field, [])):
                key = item.casefold()
                if key not in seen:
                    seen.add(key)
                    hits.append(item)
        overlaps[field] = hits
    return overlaps


def _contribution(rec: dict[str, Any], seeds: list[dict[str, Any]]) -> dict[str, float]:
    raw: dict[str, float] = {}
    for field, weight in FIELD_WEIGHTS.items():
        score = 0.0
        rec_values = _as_list(rec.get(field))
        for seed in seeds:
            score += _jaccard(rec_values, seed.get(field, []))
        raw[field] = score * weight
    total = sum(raw.values())
    if total <= 0:
        return {field: 0.0 for field in FIELD_ORDER}
    return {field: raw[field] / total for field in FIELD_ORDER}


def _headline(closest_title: str, overlaps: dict[str, list[str]]) -> str:
    if overlaps["directors"]:
        names = " & ".join(overlaps["directors"][:2])
        return f"Because you liked {closest_title} — same director ({names})"
    if overlaps["cast"]:
        names = " & ".join(overlaps["cast"][:2])
        return f"Because you liked {closest_title} — starring {names}"
    if overlaps["genres"]:
        names = " / ".join(overlaps["genres"][:2])
        return f"Because you liked {closest_title} — {names} energy"
    if overlaps["keywords"]:
        names = ", ".join(overlaps["keywords"][:2])
        return f"Because you liked {closest_title} — shared themes ({names})"
    if closest_title:
        return f"Closest in your blend to {closest_title}"
    return "Matched the overall shape of your taste blend"


def _chips(overlaps: dict[str, list[str]], limit: int = 5) -> list[str]:
    chips: list[str] = []
    for field in FIELD_ORDER:
        for item in overlaps[field]:
            if item not in chips:
                chips.append(item)
            if len(chips) >= limit:
                return chips
    return chips


def explain_pick(
    rec: dict[str, Any],
    seed_rows: list[dict[str, Any]],
    seed_indices: list[int],
    matrix,
) -> dict[str, Any]:
    overlaps = _field_overlaps(rec, seed_rows)
    closest = closest_seed(matrix, int(rec["index"]), seed_indices, seed_rows)
    return {
        "because_title": closest["title"],
        "closest_score": closest["score"],
        "overlaps": overlaps,
        "weights": _contribution(rec, seed_rows),
        "headline": _headline(closest["title"], overlaps),
        "chips": _chips(overlaps),
    }


def blend_fingerprint(seed_rows: list[dict[str, Any]], top_n: int = 6) -> dict[str, list[tuple[str, int]]]:
    """Count tags across liked movies — the Taste DNA bars for the UI."""
    fingerprint: dict[str, list[tuple[str, int]]] = {}
    for field in FIELD_ORDER:
        counter: Counter[str] = Counter()
        for seed in seed_rows:
            counter.update(_as_list(seed.get(field)))
        fingerprint[field] = counter.most_common(top_n)
    return fingerprint


def liked_profile(movies: pd.DataFrame, titles: list[str]) -> list[dict[str, Any]]:
    _, seed_rows = _seed_rows(movies, titles)
    return seed_rows


def explain_recommendations(
    catalog: dict[str, Any],
    picks: list[dict[str, Any]],
    liked_titles: list[str],
) -> list[dict[str, Any]]:
    seed_indices, seed_rows = _seed_rows(catalog["movies"], liked_titles)
    explained: list[dict[str, Any]] = []
    for pick in picks:
        enriched = dict(pick)
        enriched["why"] = explain_pick(pick, seed_rows, seed_indices, catalog["matrix"])
        explained.append(enriched)
    return explained
