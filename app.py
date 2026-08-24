import html
import os

import requests
import streamlit as st

from recommender.paths import CATALOG_PATH
from recommender.pipeline import load_catalog
from recommender.taste import recommend_blend

st.set_page_config(
    page_title="Taste DNA · Movie Recommender",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Montserrat:wght@400;600;700&display=swap');

    .main .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    .stApp { background-color: #141414; }
    div[data-testid="stVerticalBlock"] { gap: 0.4rem; }

    .main-title {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 3.2rem;
        color: #E50914;
        text-align: center;
        letter-spacing: 2px;
        margin: 0 0 0.2rem 0;
    }
    .main-sub {
        color: #A3A3A3;
        text-align: center;
        font-family: 'Montserrat', sans-serif;
        font-size: 1rem;
        margin-bottom: 1.6rem;
    }
    .section-label {
        color: #E5E5E5;
        font-size: 1.05rem;
        font-family: 'Montserrat', sans-serif;
        font-weight: 600;
        margin: 0.8rem 0 0.3rem 0;
    }
    .rec-title {
        color: #E5E5E5;
        font-family: 'Montserrat', sans-serif;
        margin-top: 1.8rem;
        margin-bottom: 1rem;
        font-size: 1.4rem;
        font-weight: 700;
    }
    .dna-wrap {
        background: #1f1f1f;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin: 1rem 0 0.4rem 0;
    }
    .dna-heading {
        color: #E50914;
        font-family: 'Bebas Neue', sans-serif;
        letter-spacing: 1px;
        font-size: 1.4rem;
        margin-bottom: 0.6rem;
    }
    .dna-row { margin-bottom: 0.55rem; }
    .dna-field {
        color: #8A8A8A;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-family: 'Montserrat', sans-serif;
        margin-bottom: 0.25rem;
    }
    .dna-chip {
        display: inline-block;
        background: #2a2a2a;
        color: #E5E5E5;
        border-radius: 999px;
        padding: 0.2rem 0.65rem;
        margin: 0 0.35rem 0.35rem 0;
        font-size: 0.8rem;
        font-family: 'Montserrat', sans-serif;
    }
    .dna-chip span { color: #E50914; font-weight: 700; }
    .movie-title {
        font-family: 'Montserrat', sans-serif;
        font-weight: 700;
        color: #E5E5E5;
        text-align: center;
        padding: 8px 6px 2px 6px;
        font-size: 0.92rem;
        min-height: 44px;
    }
    .match-line {
        color: #E50914;
        text-align: center;
        font-family: 'Montserrat', sans-serif;
        font-size: 0.78rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }
    .why-line {
        color: #B3B3B3;
        text-align: center;
        font-family: 'Montserrat', sans-serif;
        font-size: 0.74rem;
        min-height: 48px;
        padding: 0 4px;
    }
    .chip {
        display: inline-block;
        background: #2a2a2a;
        color: #E5E5E5;
        border-radius: 999px;
        padding: 0.12rem 0.5rem;
        margin: 0.12rem 0.12rem 0 0;
        font-size: 0.68rem;
        font-family: 'Montserrat', sans-serif;
    }
    .chip-row { text-align: center; min-height: 42px; }
    .stButton button {
        background-color: #E50914;
        color: white;
        font-family: 'Montserrat', sans-serif;
        font-weight: 700;
        border: none;
        padding: 12px 28px;
        border-radius: 4px;
        font-size: 1.05rem;
        width: 220px;
        margin: 16px auto;
        display: block;
    }
    .stButton button:hover { background-color: #F40612; color: white; }
    .stSelectbox div[data-baseweb="select"] > div,
    .stMultiSelect div[data-baseweb="select"] > div {
        background-color: #333333;
        color: #E5E5E5;
    }
    footer { visibility: hidden; }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_resource
def get_catalog():
    if not CATALOG_PATH.exists():
        return None
    return load_catalog()


@st.cache_data(show_spinner=False)
def fetch_poster(movie_id: int) -> str:
    api_key = os.getenv("TMDB_API_KEY", "a3621261801a2d177e73f71a8987d9df")
    try:
        response = requests.get(
            f"https://api.themoviedb.org/3/movie/{movie_id}",
            params={"api_key": api_key},
            timeout=8,
        )
        response.raise_for_status()
        poster_path = response.json().get("poster_path")
        if poster_path:
            return "https://image.tmdb.org/t/p/w500/" + poster_path
    except requests.RequestException:
        pass
    return "https://via.placeholder.com/500x750?text=No+Poster"


def render_fingerprint(fingerprint: dict) -> None:
    labels = {
        "directors": "Directors",
        "cast": "Cast",
        "genres": "Genres",
        "keywords": "Themes",
    }
    blocks = []
    for field, title in labels.items():
        items = fingerprint.get(field) or []
        if not items:
            continue
        chips = "".join(
            f'<span class="dna-chip">{html.escape(name)} <span>×{count}</span></span>'
            for name, count in items
        )
        blocks.append(
            f'<div class="dna-row"><div class="dna-field">{title}</div>{chips}</div>'
        )
    if not blocks:
        return
    st.markdown(
        '<div class="dna-wrap"><div class="dna-heading">YOUR TASTE DNA</div>'
        + "".join(blocks)
        + "</div>",
        unsafe_allow_html=True,
    )


def render_pick(pick: dict) -> None:
    why = pick.get("why") or {}
    poster = fetch_poster(pick["movie_id"])
    title = html.escape(str(pick["title"]))
    year = pick.get("release_year") or 0
    title_line = f"{title} ({year})" if year else title
    match = max(0, min(100, round(float(pick.get("score", 0)) * 100)))
    headline = html.escape(str(why.get("headline") or ""))
    chips = "".join(f'<span class="chip">{html.escape(chip)}</span>' for chip in why.get("chips") or [])
    st.image(poster, use_container_width=True)
    st.markdown(f'<div class="movie-title">{title_line}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="match-line">{match}% blend match</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="why-line">{headline}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="chip-row">{chips}</div>', unsafe_allow_html=True)


catalog = get_catalog()

st.markdown('<div class="main-title">TASTE DNA</div>', unsafe_allow_html=True)
st.markdown(
    '<p class="main-sub">Blend the movies you love. Skip the ones you do not. See why each pick landed.</p>',
    unsafe_allow_html=True,
)

if catalog is None:
    st.error("Catalog not built yet.")
    st.info("From the project folder run:  python scripts/build_catalog.py")
    st.stop()

titles = sorted(catalog["movies"]["title"].dropna().unique().tolist())

st.markdown('<p class="section-label">Movies you loved</p>', unsafe_allow_html=True)
liked = st.multiselect(
    "Movies you loved",
    titles,
    max_selections=8,
    placeholder="Pick 1–5 titles — Avatar, Inception, The Dark Knight…",
    label_visibility="collapsed",
)

st.markdown('<p class="section-label">Skip this vibe (optional)</p>', unsafe_allow_html=True)
skip_choices = ["None"] + [title for title in titles if title not in liked]
skipped = st.selectbox(
    "Skip this vibe",
    skip_choices,
    label_visibility="collapsed",
)

center = st.columns([1, 1, 1])
with center[1]:
    discover = st.button("BLEND TASTE")

if discover:
    if not liked:
        st.warning("Pick at least one movie you loved.")
    else:
        skipped_titles = [] if skipped == "None" else [skipped]
        with st.spinner("Reading your taste DNA…"):
            bundle = recommend_blend(
                catalog,
                liked_titles=liked,
                skipped_titles=skipped_titles,
                top_n=5,
            )
        render_fingerprint(bundle["fingerprint"])
        st.markdown('<h3 class="rec-title">Because of your blend</h3>', unsafe_allow_html=True)
        cols = st.columns(5)
        for i, pick in enumerate(bundle["picks"]):
            with cols[i]:
                render_pick(pick)
