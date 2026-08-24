# Taste DNA Movie Recommender

Content-based movie recommendations with a twist: you blend several movies you love (and can subtract one you do not), then the app shows a **Taste DNA** fingerprint and a **because** line for every pick.

This is not collaborative filtering. It is bag-of-words vectors from TMDB metadata (genres, top cast, directors, keywords, overview), CountVectorizer, and cosine similarity. Movie vectors are L2-normalized so a user taste query is just an average — like word2vec arithmetic:

`Avatar + Inception − The Notebook`

## Features

### Recommender engine

- **Taste Blend** — average 1–8 liked movies into one user vector; optionally subtract a skip title (`Avatar + Inception − The Notebook`)
- **Because cards** — each pick explains the overlap: shared director, cast, genres, and plot tags, plus which liked movie it is closest to
- **Taste DNA fingerprint** — frequency of directors, cast, genres, and themes across the blend, shown as a profile before the results
- **Watch-night steering** — Intense / Brainy / Comfort / Balanced nudges matching genre tokens already in the query (does not invent a mood)
- **Discovery slider** — left favors lesser-known high-rated titles (hidden gems); right favors popular crowd-pleasers
- **Structured catalog** — genres, cast, directors, keywords, ratings, and popularity are kept alongside the CountVectorizer matrix so explanations stay readable

### Product UI

- Dark cinema theme (custom Streamlit CSS, Fraunces + Manrope)
- Sidebar composer: liked titles, skip vibe, watch night, discovery mix
- Empty-state onboarding that explains blend / because / night before the first run
- Poster grid with TMDB artwork, relative match badge, because headline, and overlap chips
- Graceful fallback when `TMDB_API_KEY` is missing (letter placeholder instead of a broken image)

## Why it is different

Typical campus recommenders pick **one** movie and return the five nearest neighbors. This project treats taste as a **query you compose**:

1. Blend several titles into a single L2-normalized vector
2. Optionally subtract a vibe you want to avoid
3. Steer that query toward a watch-night mood and a discovery style
4. Rank by cosine similarity (dot product on normalized rows)
5. Explain every hit in human language, not just a score

## Setup

```bash
pip install -r requirements.txt
python scripts/build_catalog.py
```

The builder downloads the TMDB 5000 CSVs into `data/raw/` (if they are missing) and writes `artifacts/catalog.pkl`.

Posters need a free TMDB API key. Copy `.env.example` to `.env` and add your key from [themoviedb.org/settings/api](https://www.themoviedb.org/settings/api):

```bash
TMDB_API_KEY=your_tmdb_api_key_here
```

## Run

```bash
python -m streamlit run app.py
```

Pick 1–5 movies you loved, optionally skip a vibe, choose the night and discovery mix, then hit **Blend taste**.

## Project layout

```text
app.py                    Streamlit UI (theme, Taste DNA, poster cards)
recommender/taste.py      Multi-movie blend, skip subtraction, ranking
recommender/explain.py    Because headlines, overlap chips, fingerprint
recommender/nights.py     Watch-night presets and hidden-gem / crowd-pleaser mix
recommender/pipeline.py   TMDB catalog + L2-normalized CountVectorizer matrix
scripts/build_catalog.py
notebooks/project.ipynb   Original feature-engineering notebook
data/raw/                 TMDB CSVs (gitignored)
artifacts/                catalog.pkl (gitignored)
```

## Stack

Python, pandas, scikit-learn, SciPy sparse matrices, Streamlit, TMDB API
