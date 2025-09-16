# db_utils.py
import sqlite3
import os
from werkzeug.security import generate_password_hash

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'movielens.db')


def get_db_connection():
    """Tworzy nowe, krótkotrwałe połączenie z bazą danych."""
    conn = sqlite3.connect(DATABASE_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


# --- WATCHLIST ---
def get_watchlist_for_user(user_id, watched=None):
    query = 'SELECT * FROM watchlist WHERE user_id = ?'
    params = [user_id]
    if watched is not None:
        query += ' AND watched = ?'
        params.append(watched)

    with get_db_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def add_or_update_watchlist(user_id, movie_id, watched=0):
    """Dodaje film jeśli nie istnieje, albo aktualizuje watched."""
    with get_db_connection() as conn:
        existing = conn.execute(
            "SELECT 1 FROM watchlist WHERE user_id = ? AND movie_id = ?",
            (user_id, movie_id)
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE watchlist SET watched = ? WHERE user_id = ? AND movie_id = ?",
                (watched, user_id, movie_id)
            )
        else:
            conn.execute(
                "INSERT INTO watchlist (user_id, movie_id, watched) VALUES (?, ?, ?)",
                (user_id, movie_id, watched)
            )
        conn.commit()



def remove_from_watchlist(user_id, movie_id):
    with get_db_connection() as conn:
        conn.execute(
            'DELETE FROM watchlist WHERE user_id = ? AND movie_id = ?',
            (user_id, movie_id)
        )
        conn.commit()

def update_watchlist_item(user_id, movie_id, watched=None):
    if watched is None:
        return False

    query = "UPDATE watchlist SET watched = ? WHERE user_id = ? AND movie_id = ?"
    params = [watched, user_id, movie_id]

    with get_db_connection() as conn:
        conn.execute(query, params)
        conn.commit()
    return True




def mark_movie_as_watched(user_id, movie_id):
    conn = get_db_connection()
    conn.execute(
        'UPDATE watchlist SET watched = 1 WHERE user_id = ? AND movie_id = ?',
        (user_id, movie_id)
    )
    conn.commit()
    conn.close()



# ULUBIONE
def add_to_favorites(user_id, movie_id):
    query = "INSERT OR IGNORE INTO favorites (user_id, movie_id) VALUES (?, ?)"
    with get_db_connection() as conn:
        conn.execute(query, [user_id, movie_id])
        conn.commit()
    return True # już w ulubionych

def remove_from_favorites(user_id, movie_id):
    query = "DELETE FROM favorites WHERE user_id = ? AND movie_id = ?"
    with get_db_connection() as conn:
        conn.execute(query, [user_id, movie_id])
        conn.commit()
    return True

def get_favorites_for_user(user_id):
    with get_db_connection() as conn:
        rows = conn.execute(
            'SELECT f.*, m.title, m.poster_path FROM favorites f '
            'JOIN movies m ON f.movie_id = m.movie_id '
            'WHERE f.user_id = ?', (user_id,)
        ).fetchall()
    return [dict(row) for row in rows]



# --- UŻYTKOWNICY ---
def update_user_credentials(user_id, new_username=None, new_password=None):
    """
    Aktualizuje username i/lub hasło użytkownika.
    Zwraca True jeśli coś zmieniono, False jeśli nic nie zmieniono.
    """
    if not new_username and not new_password:
        return False

    with get_db_connection() as conn:
        if new_username:
            conn.execute('UPDATE users SET username = ? WHERE user_id = ?', (new_username, user_id))
        if new_password:
            hashed_pw = generate_password_hash(new_password, method='pbkdf2:sha256')
            conn.execute('UPDATE users SET password = ? WHERE user_id = ?', (hashed_pw, user_id))
        conn.commit()
    return True


def get_user_by_id(user_id):
    with get_db_connection() as conn:
        return conn.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()


# --- FILMY ---
def get_top_movies(limit=20, min_votes=1000, offset=0):
    """
    Pobiera top filmy z tabeli movies, biorąc pod uwagę minimalną liczbę głosów.
    Obsługuje paginację przez offset.
    """
    query = """
        SELECT movie_id AS id, title, poster_path, vote_average, vote_count, genres, overview
        FROM movies
        WHERE vote_average IS NOT NULL
          AND vote_count >= ?
        ORDER BY vote_average DESC, vote_count DESC
        LIMIT ? OFFSET ?
    """
    with get_db_connection() as conn:
        rows = conn.execute(query, (min_votes, limit, offset)).fetchall()

    return [dict(row) for row in rows]


def get_movie_by_id(movie_id):
    """Pobiera wszystkie dane filmu po jego ID z tabeli movies."""
    query = "SELECT * FROM movies WHERE movie_id = ? LIMIT 1"
    with get_db_connection() as conn:
        row = conn.execute(query, (movie_id,)).fetchone()
    return dict(row) if row else None


def search_movies(title=None, genre=None, year=None, keywords=None):
    query = "SELECT * FROM movies WHERE 1=1"
    params = []

    if title:
        query += " AND LOWER(title) LIKE ?"
        params.append(f"%{title.lower()}%")
    if genre:
        query += " AND LOWER(genres) LIKE ?"
        params.append(f"%{genre.lower()}%")
    if year:
        query += " AND release_year = ?"
        params.append(year)
    if keywords:
        query += " AND LOWER(keywords) LIKE ?"
        params.append(f"%{keywords.lower()}%")

    with get_db_connection() as conn:
        rows = conn.execute(query, params).fetchall()

    return [dict(row) for row in rows]

def get_all_keywords():
    """Pobiera wszystkie keywords z tabeli movies i zwraca unikalną listę słów kluczowych."""
    query = "SELECT keywords FROM movies WHERE keywords IS NOT NULL AND keywords != ''"
    keywords_set = set()

    with get_db_connection() as conn:
        rows = conn.execute(query).fetchall()
        for row in rows:
            if row["keywords"]:
                parts = [kw.strip() for kw in row["keywords"].split(",") if kw.strip()]
                keywords_set.update(parts)

    return sorted(keywords_set)

def get_all_genres():
    query = "SELECT genres FROM movies WHERE genres IS NOT NULL AND genres != ''"
    genres_set = set()
    with get_db_connection() as conn:
        rows = conn.execute(query).fetchall()
        for row in rows:
            for g in row['genres'].split('|'):
                genres_set.add(g.strip())
    return sorted(genres_set)
