import pandas as pd
from sklearn.neighbors import NearestNeighbors
from scipy.sparse import csr_matrix
import sqlite3
import os
import re

# ---- Połączenie z bazą danych ----
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'movielens.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- Normalizacja tytułów ---
def normalize_title(title):
    if not isinstance(title, str):
        return ""
    # usuń rok w nawiasach
    title = re.sub(r'\(\d{4}\)', '', title)
    title = re.sub(r'\s+', ' ', title).strip()
    return title.lower()


# --- Wczytanie i przygotowanie danych ---
def load_and_prepare_data():
    conn = None
    try:
        conn = get_db_connection()
        movies_df = pd.read_sql_query(
            "SELECT movie_id, title, clean_title, clean_title_lc, genres, overview, poster_path FROM movies",
            conn
        )
        ratings_df = pd.read_sql_query(
            "SELECT user_id, movie_id, rating FROM ratings",
            conn
        )

        print("RECOM INFO: Dane filmów i ocen załadowane z bazy danych.")

        # Konwersja typów
        movies_df['movie_id'] = pd.to_numeric(movies_df['movie_id'])
        ratings_df['movie_id'] = pd.to_numeric(ratings_df['movie_id'])
        ratings_df['user_id'] = pd.to_numeric(ratings_df['user_id'])
        ratings_df['rating'] = pd.to_numeric(ratings_df['rating'])

        # Usunięcie duplikatów
        ratings_deduplicated = ratings_df.drop_duplicates(subset=['user_id', 'movie_id'])

        # Upewnij się, że clean_title_lc jest lowercase
        movies_df['clean_title_lc'] = movies_df['clean_title'].str.lower()

        # Słownik: normalized_clean_title -> movie_id
        movie_title_to_id = pd.Series(movies_df.movie_id.values, index=movies_df['clean_title_lc']).to_dict()

        # Macierz użytkownik-film
        movie_user_mat = ratings_deduplicated.pivot(index='movie_id', columns='user_id', values='rating').fillna(0)
        movie_user_mat_sparse = csr_matrix(movie_user_mat.values)
        print("RECOM INFO: Macierz użytkownik-film utworzona.")

        # Trening modelu KNN
        model_knn = NearestNeighbors(metric='cosine', algorithm='brute')
        model_knn.fit(movie_user_mat_sparse)
        print("RECOM INFO: Model KNN wytrenowany.")

        return movies_df, movie_user_mat, movie_user_mat_sparse, model_knn, movie_title_to_id

    except Exception as e:
        print(f"BŁĄD: Nie udało się załadować danych: {e}")
        raise RuntimeError(f"Nie udało się załadować danych rekomendacji: {e}")
    finally:
        if conn:
            conn.close()


# --- Globalne zmienne ---
movies = None
movie_user_mat = None
movie_user_mat_sparse = None
model_knn = None
movie_title_to_id = None

try:
    movies, movie_user_mat, movie_user_mat_sparse, model_knn, movie_title_to_id = load_and_prepare_data()
except RuntimeError:
    exit(1)


# --- Pobranie wszystkich tytułów filmów (dla autouzupełniania) ---
def get_all_original_movie_titles():
    if movies is None or movies.empty:
        return []
    return movies[['title', 'poster_path']].dropna(subset=['title']).to_dict(orient='records')


# --- Funkcja rekomendacji ---
def get_recommendations(movie_title_from_frontend, n=5, exclude_titles=None):
    if not movie_title_from_frontend or not movie_title_from_frontend.strip():
        return []

    if exclude_titles is None:
        exclude_titles = []

    target_movie_for_lookup = normalize_title(movie_title_from_frontend)
    movie_id = movie_title_to_id.get(target_movie_for_lookup)

    if movie_id is None or movie_id not in movie_user_mat.index:
        return []

    movie_idx_in_mat = movie_user_mat.index.get_loc(movie_id)
    num_movies_in_mat = movie_user_mat_sparse.shape[0]
    num_neighbors_to_fetch = min(num_movies_in_mat, max(n + 1, len(exclude_titles) + n + 25))

    distances, indices = model_knn.kneighbors(
        movie_user_mat_sparse[movie_idx_in_mat],
        n_neighbors=num_neighbors_to_fetch
    )

    similar_ids = [movie_user_mat.index[i] for i in indices.flatten()[1:] if i < num_movies_in_mat]
    all_potential_movies_df = movies[movies['movie_id'].isin(similar_ids)]
    all_potential_titles = all_potential_movies_df['title'].dropna().tolist()

    normalized_exclude_titles = {normalize_title(t) for t in exclude_titles}
    normalized_input_title_for_exclude = normalize_title(movie_title_from_frontend)

    final_recommendations = []
    seen_in_batch = set()

    for original_title in all_potential_titles:
        normalized_current_title = normalize_title(original_title)
        if normalized_current_title not in normalized_exclude_titles and \
           normalized_current_title != normalized_input_title_for_exclude and \
           normalized_current_title not in seen_in_batch:

            movie_row = movies[movies['title'] == original_title].iloc[0]
            final_recommendations.append({
                "id": movie_row["movie_id"], 
                "title": original_title,
                "overview": movie_row.get("overview", "Brak opisu"),
                "poster_path": movie_row.get("poster_path", None)
            })
            seen_in_batch.add(normalized_current_title)
            if len(final_recommendations) >= n:
                break

    return final_recommendations


# --- Pobranie szczegółów filmu ---
def get_movie_details(movie_title):
    if movies is None or movies.empty:
        return {
            "title": movie_title,
            "poster_path": None,
            "overview": None
        }

    movie_row = movies[movies['title'] == movie_title]

    if movie_row.empty:
        norm_title = normalize_title(movie_title)
        movie_row = movies[movies['clean_title_lc'] == norm_title]

    if not movie_row.empty:
        row = movie_row.iloc[0]
        return {
            "title": row["title"],
            "poster_path": row.get("poster_path", None),
            "overview": row.get("overview", None)
        }

    return {
        "title": movie_title,
        "poster_path": None,
        "overview": None
    }


def get_movie_full_details(title_with_year):
    """Pobiera pełne dane o filmie z tabeli movies."""
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT * FROM movies WHERE title = ?",
            (title_with_year,)
        ).fetchone()
        if row:
            movie_data = dict(row)
            movie_data['genres'] = movie_data['genres'].split("|") if movie_data.get('genres') else []
            return movie_data
    return {}
