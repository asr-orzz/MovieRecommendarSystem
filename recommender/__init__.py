"""Content-based movie engine with blendable Taste DNA vectors."""

from .explain import blend_fingerprint, explain_recommendations
from .pipeline import build_catalog, load_catalog, save_catalog
from .taste import UnknownMovieError, recommend_blend

__all__ = [
    "UnknownMovieError",
    "blend_fingerprint",
    "build_catalog",
    "explain_recommendations",
    "load_catalog",
    "recommend_blend",
    "save_catalog",
]
