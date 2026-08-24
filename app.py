import html
import os

import requests
import streamlit as st

from recommender.nights import NIGHT_LABELS
from recommender.paths import CATALOG_PATH, load_env
from recommender.pipeline import load_catalog
from recommender.taste import recommend_blend

load_env()

st.set_page_config(
    page_title="Taste DNA",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

THEME = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,560;9..144,700&family=Manrope:wght@400;500;600;700&display=swap');

    :root {
        --bg: #09090b;
        --panel: #121216;
        --panel-2: #18181f;
        --line: rgba(255,255,255,0.08);
        --text: #f4f4f5;
        --muted: #a1a1aa;
        --soft: #71717a;
        --accent: #fb7185;
        --accent-2: #fda4af;
        --good: #4ade80;
    }

    html, body, [data-testid="stAppViewContainer"], .stApp {
        background: var(--bg);
        color: var(--text);
        font-family: 'Manrope', sans-serif;
    }

    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stToolbar"] { visibility: hidden; }
    footer { visibility: hidden; }
    #MainMenu { visibility: hidden; }

    .main .block-container {
        padding: 1.6rem 2rem 3rem 2rem;
        max-width: 1320px;
    }

    [data-testid="stSidebar"] {
        background: #0c0c10;
        border-right: 1px solid var(--line);
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: var(--muted); }
    [data-testid="stSidebar"] .stButton button {
        width: 100%;
        background: var(--accent);
        color: #19060a;
        border: 0;
        border-radius: 12px;
        font-family: 'Manrope', sans-serif;
        font-weight: 700;
        letter-spacing: 0.04em;
        padding: 0.75rem 1rem;
        margin-top: 0.4rem;
    }
    [data-testid="stSidebar"] .stButton button:hover {
        background: var(--accent-2);
        color: #19060a;
    }

    .brand {
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        gap: 1rem;
        margin-bottom: 1.4rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid var(--line);
    }
    .brand-mark {
        font-family: 'Fraunces', serif;
        font-size: 2rem;
        letter-spacing: -0.03em;
        color: var(--text);
        margin: 0;
    }
    .brand-mark span { color: var(--accent); }
    .brand-kicker {
        color: var(--soft);
        font-size: 0.78rem;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        margin: 0 0 0.25rem 0;
    }
    .brand-side {
        color: var(--muted);
        font-size: 0.88rem;
        text-align: right;
        max-width: 360px;
        line-height: 1.45;
    }

    .hero-empty {
        background:
            radial-gradient(800px 280px at 10% 0%, rgba(251,113,133,0.16), transparent 55%),
            linear-gradient(180deg, var(--panel) 0%, #0d0d11 100%);
        border: 1px solid var(--line);
        border-radius: 22px;
        padding: 2.2rem 2rem;
        margin-top: 0.4rem;
    }
    .hero-empty h2 {
        font-family: 'Fraunces', serif;
        font-size: 2.1rem;
        letter-spacing: -0.03em;
        margin: 0 0 0.6rem 0;
    }
    .hero-empty p {
        color: var(--muted);
        max-width: 620px;
        line-height: 1.6;
        margin: 0 0 1.4rem 0;
    }
    .feature-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.8rem; }
    .feature {
        background: rgba(255,255,255,0.03);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 1rem 1rem 0.95rem 1rem;
    }
    .feature b { display: block; margin-bottom: 0.25rem; color: var(--text); }
    .feature span { color: var(--soft); font-size: 0.86rem; line-height: 1.45; }

    .dna-wrap {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 20px;
        padding: 1.15rem 1.25rem 0.85rem 1.25rem;
        margin: 0.2rem 0 1.1rem 0;
    }
    .dna-top {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        gap: 1rem;
        margin-bottom: 0.85rem;
    }
    .dna-heading {
        font-family: 'Fraunces', serif;
        font-size: 1.35rem;
        margin: 0;
    }
    .dna-meta { color: var(--soft); font-size: 0.82rem; }
    .dna-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.75rem; }
    .dna-col {
        background: var(--panel-2);
        border-radius: 14px;
        padding: 0.75rem 0.8rem;
        border: 1px solid var(--line);
    }
    .dna-field {
        color: var(--soft);
        font-size: 0.68rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 0.45rem;
    }
    .dna-chip {
        display: flex;
        justify-content: space-between;
        gap: 0.5rem;
        color: var(--text);
        font-size: 0.8rem;
        padding: 0.22rem 0;
        border-bottom: 1px solid rgba(255,255,255,0.04);
    }
    .dna-chip:last-child { border-bottom: 0; }
    .dna-chip em { color: var(--accent-2); font-style: normal; font-weight: 700; }

    .section-head {
        display: flex;
        justify-content: space-between;
        align-items: end;
        margin: 0.4rem 0 0.9rem 0;
    }
    .section-head h3 {
        font-family: 'Fraunces', serif;
        font-size: 1.45rem;
        margin: 0;
    }
    .section-head p { color: var(--soft); font-size: 0.84rem; margin: 0; }

    .poster-card {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 16px;
        overflow: hidden;
        min-height: 100%;
    }
    .poster-frame {
        position: relative;
        aspect-ratio: 2 / 3;
        background: linear-gradient(160deg, #1f1f27, #0b0b0e);
    }
    .poster-frame img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
    }
    .poster-fallback {
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'Fraunces', serif;
        font-size: 2.4rem;
        color: var(--accent-2);
    }
    .match-badge {
        position: absolute;
        top: 10px;
        right: 10px;
        background: rgba(9,9,11,0.82);
        border: 1px solid rgba(251,113,133,0.35);
        color: var(--accent-2);
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        padding: 0.22rem 0.45rem;
        border-radius: 999px;
    }
    .poster-body { padding: 0.8rem 0.85rem 0.95rem 0.85rem; }
    .poster-title {
        font-weight: 700;
        font-size: 0.95rem;
        line-height: 1.3;
        margin-bottom: 0.2rem;
    }
    .poster-title span { color: var(--soft); font-weight: 500; font-size: 0.8rem; }
    .poster-why {
        color: var(--muted);
        font-size: 0.76rem;
        line-height: 1.4;
        min-height: 3.2em;
        margin: 0.35rem 0 0.5rem 0;
    }
    .chip {
        display: inline-block;
        background: rgba(255,255,255,0.05);
        border: 1px solid var(--line);
        color: #d4d4d8;
        border-radius: 999px;
        padding: 0.12rem 0.45rem;
        margin: 0 0.2rem 0.2rem 0;
        font-size: 0.66rem;
    }

    .sidebar-brand {
        font-family: 'Fraunces', serif;
        font-size: 1.15rem;
        margin: 0.2rem 0 0.15rem 0;
    }
    .sidebar-note { color: var(--soft); font-size: 0.8rem; margin-bottom: 0.8rem; }

    .stSelectbox div[data-baseweb="select"] > div,
    .stMultiSelect div[data-baseweb="select"] > div {
        background: #16161c;
        border-color: var(--line);
        color: var(--text);
        border-radius: 10px;
    }
    [data-testid="stSlider"] { padding-top: 0.2rem; }

    @media (max-width: 1100px) {
        .dna-grid, .feature-grid { grid-template-columns: 1fr 1fr; }
        .brand { flex-direction: column; align-items: flex-start; }
        .brand-side { text-align: left; }
    }
</style>
"""

st.markdown(THEME, unsafe_allow_html=True)


@st.cache_resource
def get_catalog():
    if not CATALOG_PATH.exists():
        return None
    return load_catalog()


@st.cache_data(show_spinner=False)
def fetch_poster(movie_id: int) -> str:
    api_key = os.getenv("TMDB_API_KEY", "").strip()
    if not api_key:
        return ""
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
    return ""


def discovery_copy(value: float) -> str:
    if value < -0.1:
        return "Hidden gems"
    if value > 0.1:
        return "Crowd-pleasers"
    return "Balanced discovery"


def render_header() -> None:
    st.markdown(
        """
        <div class="brand">
            <div>
                <p class="brand-kicker">Content recommender</p>
                <p class="brand-mark">Taste <span>DNA</span></p>
            </div>
            <div class="brand-side">Blend the films you love. Subtract a vibe you do not. Every pick arrives with a reason.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state() -> None:
    st.markdown(
        """
        <div class="hero-empty">
            <h2>Build a taste query, not a one-movie clone.</h2>
            <p>Choose a few titles in the panel. The engine averages their vectors, can subtract a skip, then explains the overlap — director, cast, genres, themes.</p>
            <div class="feature-grid">
                <div class="feature"><b>Taste Blend</b><span>Avatar + Inception − The Notebook becomes one user vector.</span></div>
                <div class="feature"><b>Because cards</b><span>Each poster says why it landed, not just a cosine score.</span></div>
                <div class="feature"><b>Watch night</b><span>Steer toward intense, brainy, or comfort — and hidden gems.</span></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_fingerprint(fingerprint: dict, night_label: str, mix: str) -> None:
    labels = {
        "directors": "Directors",
        "cast": "Cast",
        "genres": "Genres",
        "keywords": "Themes",
    }
    columns = []
    for field, title in labels.items():
        items = list(fingerprint.get(field) or [])
        if not items:
            items = [("—", 0)]
        chips = "".join(
            f'<div class="dna-chip"><span>{html.escape(str(name))}</span><em>×{count}</em></div>'
            if count
            else f'<div class="dna-chip"><span>{html.escape(str(name))}</span><em></em></div>'
            for name, count in items[:5]
        )
        columns.append(f'<div class="dna-col"><div class="dna-field">{title}</div>{chips}</div>')
    st.markdown(
        f"""
        <div class="dna-wrap">
            <div class="dna-top">
                <p class="dna-heading">Your Taste DNA</p>
                <p class="dna-meta">{html.escape(night_label)} · {html.escape(mix)}</p>
            </div>
            <div class="dna-grid">{''.join(columns)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_pick(pick: dict, relative: int) -> None:
    why = pick.get("why") or {}
    poster = fetch_poster(pick["movie_id"])
    title = html.escape(str(pick["title"]))
    year = pick.get("release_year") or 0
    year_html = f"<span> {year}</span>" if year else ""
    headline = html.escape(str(why.get("headline") or "Matched the shape of your blend"))
    chips = "".join(f'<span class="chip">{html.escape(chip)}</span>' for chip in (why.get("chips") or [])[:4])
    if poster:
        art = f'<img src="{html.escape(poster)}" alt="{title}">'
    else:
        art = f'<div class="poster-fallback">{title[:1]}</div>'
    st.markdown(
        f"""
        <div class="poster-card">
            <div class="poster-frame">{art}<div class="match-badge">{relative}%</div></div>
            <div class="poster-body">
                <div class="poster-title">{title}{year_html}</div>
                <div class="poster-why">{headline}</div>
                <div>{chips}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def relative_matches(picks: list[dict]) -> list[int]:
    peak = max((float(pick.get("score") or 0) for pick in picks), default=0) or 1.0
    return [max(8, min(100, round(float(pick.get("score") or 0) / peak * 100))) for pick in picks]


catalog = get_catalog()
render_header()

if catalog is None:
    st.error("Catalog not built yet.")
    st.info("From the project folder run:  `python scripts/build_catalog.py`")
    st.stop()

titles = sorted(catalog["movies"]["title"].dropna().unique().tolist())

with st.sidebar:
    st.markdown('<p class="sidebar-brand">Compose a blend</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sidebar-note">Start with 2–5 films you actually like. One title still works; a blend stands out.</p>',
        unsafe_allow_html=True,
    )
    liked = st.multiselect(
        "Movies you loved",
        titles,
        max_selections=8,
        placeholder="Inception, The Dark Knight…",
    )
    skip_choices = ["None"] + [title for title in titles if title not in liked]
    skipped = st.selectbox("Skip this vibe", skip_choices)
    night = st.radio(
        "Watch night",
        list(NIGHT_LABELS.keys()),
        format_func=lambda key: NIGHT_LABELS[key],
    )
    discovery = st.slider(
        "Discovery",
        min_value=-1.0,
        max_value=1.0,
        value=0.0,
        step=0.25,
        help="Left favors lesser-known high-rated titles. Right favors popular ones.",
    )
    left, right = st.columns(2)
    left.caption("Hidden gems")
    right.caption("Crowd-pleasers")
    blend_clicked = st.button("Blend taste")
    if not os.getenv("TMDB_API_KEY", "").strip():
        st.caption("Add TMDB_API_KEY to a local .env file to load posters.")

params = (tuple(liked), skipped, night, float(discovery))
if "bundle" not in st.session_state:
    st.session_state.bundle = None
    st.session_state.params = None
    st.session_state.has_blended = False

if blend_clicked and not liked:
    st.warning("Pick at least one movie you loved.")
elif blend_clicked and liked:
    st.session_state.has_blended = True
    st.session_state.params = None

if liked and st.session_state.has_blended and st.session_state.params != params:
    skipped_titles = [] if skipped == "None" else [skipped]
    with st.spinner("Reading your taste DNA…"):
        st.session_state.bundle = recommend_blend(
            catalog,
            liked_titles=liked,
            skipped_titles=skipped_titles,
            top_n=5,
            night=night,
            discovery=discovery,
        )
    st.session_state.params = params

bundle = st.session_state.bundle
if not bundle:
    render_empty_state()
else:
    night_label = NIGHT_LABELS.get(bundle.get("night"), "Balanced")
    mix = discovery_copy(float(bundle.get("discovery") or 0))
    render_fingerprint(bundle["fingerprint"], night_label, mix)
    st.markdown(
        f"""
        <div class="section-head">
            <h3>Because of your blend</h3>
            <p>{html.escape(night_label)} · {html.escape(mix)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    picks = bundle["picks"]
    rels = relative_matches(picks)
    cols = st.columns(5)
    for column, pick, relative in zip(cols, picks, rels):
        with column:
            render_pick(pick, relative)
