# Taste DNA Movie Recommender

Content-based movie recommendations with a twist: you blend several movies you love (and can subtract one you do not), then the app shows a **Taste DNA** fingerprint and a **because** line for every pick.

This is not collaborative filtering. It is bag-of-words vectors from TMDB metadata (genres, top cast, directors, keywords, overview), CountVectorizer, and cosine similarity. Movie vectors are L2-normalized so a user taste query is just an average — like word2vec arithmetic:

`Avatar + Inception − The Notebook`

## Why it is different

- **Taste Blend** — multi-movie user vector, optional skip
- **Because cards** — shared director, cast, genres, and plot tags
- **Watch-night controls** — Intense / Brainy / Comfort, plus hidden gems vs crowd-pleasers

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

Pick 1–5 movies you loved, optionally skip a vibe, choose the night, then hit **BLEND TASTE**.

## Project layout

```text
app.py                 Streamlit UI
recommender/           blend, explain, night steering, catalog pipeline
scripts/build_catalog.py
notebooks/project.ipynb   original feature-engineering notebook
data/raw/              TMDB CSVs (gitignored)
artifacts/             catalog.pkl (gitignored)
```
