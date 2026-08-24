"""Content-based movie engine with blendable Taste DNA vectors."""

from .pipeline import build_catalog, load_catalog, save_catalog
from .taste import UnknownMovieError, recommend_blend

__all__ = [
    "UnknownMovieError",
    "build_catalog",
    "load_catalog",
    "recommend_blend",
    "save_catalog",
]
