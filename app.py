import streamlit as st
import pandas as pd
import pickle
import requests

# Page configuration with dark theme
st.set_page_config(
    page_title="Movie Recommender System",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Netflix-like styling
st.markdown("""
<style>
    /* Import Netflix Sans font */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,100..900;1,100..900&display=swap');

    /* Remove whitespace and padding from the main container */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 100%;
    }

    /* Netflix dark background */
    .stApp {
        background-color: #141414;
    }

    /* Remove padding/margin that creates white space */
    div[data-testid="stVerticalBlock"] {
        gap: 0rem;
    }

    /* Main title styling - Netflix style */
    .main-title {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 3.5rem;
        color: #E50914;
        text-align: center;
        margin-bottom: 2rem;
        display: flex;
        align-items: center;
        justify-content: center;
        letter-spacing: 1px;
    }

    /* Selection label */
    .selection-label {
        color: #E5E5E5;
        font-size: 1.2rem;
        margin-bottom: 0.5rem;
        font-family: 'Arial', sans-serif;
    }

    /* Recommendations title */
    .rec-title {
        color: #E5E5E5;
        font-family: 'Arial', sans-serif;
        margin-top: 2rem;
        margin-bottom: 1.5rem;
        font-size: 1.5rem;
        font-weight: bold;
    }

    /* Movie card styling */
    .movie-container {
        transition: transform 0.3s;
        margin-bottom: 1rem;
    }

    .movie-container:hover {
        transform: scale(1.05);
    }

    .movie-card {
        border-radius: 4px;
        overflow: hidden;
        box-shadow: 0 0 10px rgba(0,0,0,0.5);
    }

    .movie-title {
        font-family: 'Arial', sans-serif;
        font-weight: bold;
        color: #E5E5E5;
        text-align: center;
        padding: 10px;
        font-size: 1rem;
        background-color: rgba(0, 0, 0, 0.7);
        white-space: normal;
        height: 60px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    /* Button styling - Netflix red */
    .stButton button {
        background-color: #E50914;
        color: white;
        font-family: 'Arial', sans-serif;
        font-weight: bold;
        border: none;
        padding: 12px 24px;
        border-radius: 4px;
        font-size: 1.1rem;
        cursor: pointer;
        transition: background-color 0.3s;
        width: 180px;
        text-align: center;
        margin: 20px auto;
        display: block;
    }

    .stButton button:hover {
        background-color: #F40612;
        color:white;
    }

    /* Selector styling */
    .stSelectbox div[data-baseweb="select"] {
        background-color: #333333;
        border: none;
        border-radius: 4px;
    }

    .stSelectbox div[data-baseweb="select"] > div {
        background-color: #333333;
        color: #E5E5E5;
        font-family: 'Arial', sans-serif;
    }

    /* Remove streamlit footer */
    footer {
        visibility: hidden;
    }

    /* Hide hamburger menu */
    header {
        visibility: hidden;
    }
</style>
""", unsafe_allow_html=True)


def fetch_poster(movie_id):
    response = requests.get(f'https://api.themoviedb.org/3/movie/{movie_id}?api_key=a3621261801a2d177e73f71a8987d9df')
    data = response.json()
    poster_path = data.get('poster_path')
    if poster_path:
        return "https://image.tmdb.org/t/p/w500/" + poster_path
    else:
        return "https://via.placeholder.com/500x750?text=No+Poster+Available"


def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommended_movies = []
    recommended_movies_posters = []
    for i in movies_list:
        movie_id = movies.iloc[i[0]].movie_id
        recommended_movies.append(movies.iloc[i[0]].title)
        recommended_movies_posters.append(fetch_poster(movie_id))
    return recommended_movies, recommended_movies_posters


# Load data
try:
    movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
    movies = pd.DataFrame(movies_dict)
    similarity = pickle.load(open('similarity.pkl', 'rb'))

    # App header
    st.markdown('<div class="main-title">MOVIE RECOMMENDER SYSTEM</div>', unsafe_allow_html=True)

    # Movie selection
    st.markdown('<p class="selection-label">Select a movie you like:</p>', unsafe_allow_html=True)
    selected_movie_name = st.selectbox(
        '',  # Empty label since we added it above
        movies['title'].values
    )

    # Single DISCOVER button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        discover_button = st.button("DISCOVER")

    # Recommendations section
    if discover_button:
        with st.spinner(''):
            names, posters = recommend(selected_movie_name)

            st.markdown('<h3 class="rec-title">Here are some movies you might enjoy:</h3>', unsafe_allow_html=True)

            # Use columns for movie display
            cols = st.columns(5)

            for i, col in enumerate(cols):
                with col:
                    st.markdown(f'<div class="movie-container">', unsafe_allow_html=True)
                    st.markdown(f'<div class="movie-card">', unsafe_allow_html=True)
                    st.image(posters[i])
                    st.markdown(f'<div class="movie-title">{names[i]}</div>', unsafe_allow_html=True)
                    st.markdown('</div></div>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"An error occurred: {e}")
    st.info(
        "Please make sure you have the required data files (movie_dict.pkl and similarity.pkl) in the same directory as this app.")