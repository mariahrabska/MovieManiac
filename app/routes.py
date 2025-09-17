# routes.py
import json
from flask import Blueprint, flash, render_template, request, jsonify, session, redirect, url_for
from .recommender import (
    get_recommendations,
    get_all_original_movie_titles,
    get_movie_full_details,
    get_movie_details
)
from .db_utils import (
    get_all_genres,
    get_watchlist_for_user,
    add_or_update_watchlist,
    remove_from_watchlist,
    update_user_credentials,
    get_user_by_id,
    get_top_movies,
    get_movie_by_id,
    add_to_favorites,
    remove_from_favorites,
    get_favorites_for_user
)

main = Blueprint('main', __name__)

# --- Strony główne ---
@main.route("/", methods=["GET"])
def index():
    return redirect(url_for('main.dashboard')) if 'user_id' in session else redirect(url_for('auth.login'))

@main.route("/dashboard", methods=["GET"])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template("dashboard.html")

@main.route("/get_movie_titles", methods=["GET"])
def get_movie_titles():
    all_titles = get_all_original_movie_titles()
    return jsonify(all_titles)

# --- Rekomendacje ---
@main.route("/recommend", methods=["POST"])
def recommend():
    if 'user_id' not in session:
        flash('Musisz być zalogowany, aby zobaczyć rekomendacje.', 'info')
        return redirect(url_for('auth.login'))

    movie_title_raw = request.form.get("movie")
    movie_title = movie_title_raw.strip().strip('"') if movie_title_raw else None

    if not movie_title:
        flash('Nie wybrano filmu do rekomendacji.', 'error')
        return redirect(url_for('main.dashboard'))

    # pobieramy 20 rekomendacji
    recommendations = get_recommendations(movie_title, n=20)
    selected_movie = get_movie_details(movie_title)

    user_id = session['user_id']
    watchlist_entries = get_watchlist_for_user(user_id, watched=0)
    watched_entries = get_watchlist_for_user(user_id, watched=1)

    watchlist_ids = [m['movie_id'] for m in watchlist_entries]
    watched_ids = [m['movie_id'] for m in watched_entries]

    return render_template(
        "recommendations.html",
        movie=selected_movie,
        recommendations=recommendations,
        watchlist_ids=watchlist_ids,
        watched_ids=watched_ids,
        favorite_ids=[m['movie_id'] for m in get_favorites_for_user(user_id)]
    )





@main.route('/get_new_recommendations', methods=['POST'])
def get_new_recommendations():
    if 'user_id' not in session:
        return jsonify({'error': 'Nieautoryzowany dostęp'}), 401

    from .recommender import normalize_title

    data = request.get_json() or {}
    movie_title = data.get('movie_title', '')
    displayed_raw = data.get('displayed_titles', [])

    # normalizacja tytułów
    displayed_norm = []
    for x in displayed_raw:
        if isinstance(x, dict) and 'title' in x:
            displayed_norm.append(normalize_title(x['title']))
        elif isinstance(x, str):
            displayed_norm.append(normalize_title(x))

    movie_norm = normalize_title(movie_title)
    exclude_titles = list(set(displayed_norm + [movie_norm]))

    new_recs = get_recommendations(movie_title, n=5, exclude_titles=exclude_titles)

    user_id = session['user_id']
    user_watchlist = get_watchlist_for_user(user_id)
    user_watchlist_ids = [m['movie_id'] for m in user_watchlist]

    # używamy movie_id zamiast tytułu
    final_recs = []
    for rec in new_recs:
        rec['in_watchlist'] = rec['id'] in user_watchlist_ids
        final_recs.append(rec)

    return jsonify({'recommendations': final_recs})

# --- Watchlist ---
@main.route('/movies-list', methods=['GET'])
def movies_list():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for('auth.login'))

    watchlist_entries = get_watchlist_for_user(user_id, watched=0)

    watchlist_movies = []
    keywords_set = set()  # zbieramy unikalne keywords do filtra

    for entry in watchlist_entries:
        movie_id = entry['movie_id']
        movie_data = get_movie_by_id(movie_id)
        if movie_data:
            watchlist_movies.append({
                'id': movie_data.get('movie_id'),
                'title': movie_data.get('title'),
                'poster_path': movie_data.get('poster_path'),
                'genres': movie_data.get('genres', ""),   # np. "Action|Drama"
                'release_year': movie_data.get('release_year'),
                'keywords': movie_data.get('keywords', "")  # <- dodane
            })
            # Dodajemy do setu, jeśli chcesz mieć dropdown keywords
            if movie_data.get('keywords'):
                keywords_set.update(movie_data['keywords'].split('|'))

    # lista ID ulubionych
    favorite_entries = get_favorites_for_user(user_id)
    favorite_ids = [f['movie_id'] for f in favorite_entries]

    return render_template(
        "movies-list.html",
        watchlist=watchlist_movies,
        favorite_ids=favorite_ids,
        genres=sorted({g for m in watchlist_movies for g in m['genres'].split('|') if g}),
        keywords=sorted(keywords_set)  # jeśli chcesz dropdown keywords
    )

@main.route('/add_to_watchlist', methods=['POST'])
def add_to_watchlist_route():
    data = request.get_json()
    movie_id = int(data.get('movie_id'))
    watched = int(data.get('watched', 0))
    add_or_update_watchlist(session['user_id'], movie_id, watched)
    return jsonify({'success': True})



@main.route('/remove_from_watchlist', methods=['POST'])
def remove_from_watchlist_route():
    data = request.get_json()
    movie_id = int(data.get('movie_id'))
    if not movie_id:
        return jsonify(success=False, error="Nie podano ID filmu"), 400

    user_id = session.get('user_id')
    watchlist = get_watchlist_for_user(user_id)
    if movie_id not in [m['movie_id'] for m in watchlist]:
        return jsonify(success=False, error="Film nie znajduje się na Twojej liście"), 404

    remove_from_watchlist(user_id, movie_id)
    return jsonify(success=True)



@main.route('/mark_as_watched', methods=['POST'])
def mark_as_watched_route():
    if 'user_id' not in session:
        return jsonify({'error': 'Nieautoryzowany'}), 401

    data = request.get_json()
    movie_id = data.get('movie_id')  # zmieniamy na ID
    if not movie_id:
        return jsonify({'error': 'Brak ID filmu'}), 400

    movie_id = int(movie_id)

    from .db_utils import mark_movie_as_watched
    mark_movie_as_watched(session['user_id'], movie_id)
    return jsonify({'success': True})


@main.route('/watched/remove', methods=['POST'])
def remove_from_watched():
    if 'user_id' not in session:
        return jsonify({'error': 'Nieautoryzowany'}), 401

    data = request.get_json()
    movie_id = data.get('movie_id')
    if not movie_id:
        return jsonify({'error': 'Brak ID filmu'}), 400

    movie_id = int(movie_id)
    from .db_utils import update_watchlist_item
    success = update_watchlist_item(session['user_id'], movie_id, watched=0)
    return jsonify({'success': success})



@main.route('/favorites/add', methods=['POST'])
def add_to_favorites_route():
    if 'user_id' not in session:
        return jsonify({'error': 'Nieautoryzowany'}), 401
    data = request.get_json()
    movie_id = data.get('movie_id')
    if not movie_id:
        return jsonify({'error': 'Brak ID filmu'}), 400
    success = add_to_favorites(session['user_id'], movie_id)
    return jsonify({'success': success})


@main.route('/favorites/toggle', methods=['POST'])
def toggle_favorite():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Nieautoryzowany'}), 401

    data = request.get_json()
    movie_id = data.get('movie_id')
    if not movie_id:
        return jsonify({'success': False, 'error': 'Brak ID filmu'}), 400

    user_id = session['user_id']

    # Sprawdzamy, czy film jest już w ulubionych
    current_favorites = get_favorites_for_user(user_id)
    favorite_ids = [f['movie_id'] for f in current_favorites]

    if int(movie_id) in favorite_ids:
        # Usuń z ulubionych
        remove_from_favorites(user_id, movie_id)
        return jsonify({'success': True, 'favorited': False})
    else:
        # Dodaj do ulubionych
        add_to_favorites(user_id, movie_id)
        return jsonify({'success': True, 'favorited': True})


# --- Ustawienia konta ---
@main.route('/settings', methods=['GET', 'POST'])
def settings():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    user = get_user_by_id(user_id)
    if not user:
        flash("Nie znaleziono użytkownika.", "error")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        new_username = request.form.get('username', '').strip()
        new_password = request.form.get('password', '').strip()

        if not new_username:
            flash("Username nie może być pusty.", "error")
            return redirect(url_for('main.settings'))

        updated = update_user_credentials(user_id, new_username, new_password)
        if updated:
            session['username'] = new_username
            flash("Account settings updated!", "success")
        else:
            flash("No changes.", "info")

        return redirect(url_for('main.settings'))

    return render_template("settings.html", username=user['username'])

import re

@main.route('/movie_details', methods=['POST'])
def movie_details():
    if 'user_id' not in session:
        return jsonify({'error': 'Nieautoryzowany dostęp'}), 401

    data = request.get_json()
    movie_id = data.get('movie_id')
    if not movie_id:
        return jsonify({'error': 'Brak ID filmu'}), 400

    movie_data = get_movie_by_id(movie_id)
    if not movie_data:
        return jsonify({'error': 'Nie znaleziono filmu'}), 404

    response = {
        "title": movie_data["title"],
        "poster_path": movie_data.get("poster_path"),
        "overview": movie_data.get("overview"),
        "genres": movie_data.get("genres", "").split("|") if movie_data.get("genres") else [],
        "release_year": movie_data.get("release_year"),
        "production_companies": movie_data.get("production_companies", "").split("|") if movie_data.get("production_companies") else [],
        "production_countries": movie_data.get("production_countries", "").split("|") if movie_data.get("production_countries") else [],
        "vote_average": movie_data.get("vote_average")
    }
    return jsonify(response)




@main.route("/ranking", methods=["GET"])
def ranking():
    page = int(request.args.get("page", 1))
    per_page = 20
    offset = (page - 1) * per_page

    top_movies = get_top_movies(limit=per_page, min_votes=1000, offset=offset)

    return render_template(
        "ranking.html",
        top_movies=top_movies,
        page=page
    )

@main.route("/movie/<int:movie_id>", methods=["GET"])
def movie_page(movie_id):
    movie = get_movie_by_id(movie_id)  # funkcja w db_utils.py
    if not movie:
        flash("Nie znaleziono filmu.", "error")
        return redirect(url_for("main.ranking"))
    
    return render_template("movie.html", movie=movie)


@main.route('/all_genres')
def all_genres():
    genres = get_all_genres()  # funkcja z db_utils.py
    return jsonify(genres)


@main.route("/search", methods=["GET", "POST"])
def search():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    results = None
    title = request.form.get("title", "").strip()
    genre = request.form.get("genre", "").strip()
    year = request.form.get("year", "").strip()
    keywords = request.form.get("keywords", "").strip()

    genres = get_all_genres()


    if request.method == "POST":
        # 👇 tu możesz dopasować logikę do swojego db_utils / recommender
        from .db_utils import search_movies  # zakładamy, że dodasz taką funkcję

        results = search_movies(
            title=title if title else None,
            genre=genre if genre else None,
            year=year if year else None,
            keywords=keywords if keywords else None
        )

    return render_template(
        "search.html",
        results=results,
        title=title,
        genre=genre,
        year=year,
        keywords=keywords,
        genres=genres
    )

@main.route('/watched', methods=['GET'])
def watched_list():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for('auth.login'))

    watched_entries = get_watchlist_for_user(user_id, watched=1)
    full_movies = []
    genres_set = set()
    for entry in watched_entries:
        movie_data = get_movie_by_id(entry['movie_id'])
        if movie_data:
            full_movies.append(movie_data)
            # Dodajemy gatunki do setu
            if movie_data.get('genres'):
                genres_set.update(movie_data['genres'].split('|'))

    genres_list = sorted(genres_set)  # posortowane alfabetycznie

    return render_template("watched.html", watchlist=full_movies, genres=genres_list)

@main.route('/favorites', methods=['GET'])
def favorites_list():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for('auth.login'))

    favorite_entries = get_favorites_for_user(user_id)
    full_movies = []
    genres_set = set()

    for entry in favorite_entries:
        movie_data = get_movie_by_id(entry['movie_id'])
        if movie_data:
            # dodajemy pole added_at z tabeli favorites
            movie_data_copy = movie_data.copy()
            movie_data_copy['added_at'] = entry['added_date']  # <-- kluczowe
            full_movies.append(movie_data_copy)

            # zbieramy gatunki
            if movie_data.get('genres'):
                genres_set.update(movie_data['genres'].split('|'))

    genres_list = sorted(genres_set)

    return render_template("favorites.html", favorites=full_movies, genres=genres_list)


@main.route('/keywords_suggestions', methods=['GET'])
def keywords_suggestions():
    q = request.args.get('q', '').lower()
    user_id = session.get('user_id')
    watchlist = get_watchlist_for_user(user_id)
    
    keywords_set = set()
    for entry in watchlist:
        movie = get_movie_by_id(entry['movie_id'])
        if movie and movie.get('keywords'):
            for kw in movie['keywords'].split('|'):
                if q in kw.lower():
                    keywords_set.add(kw)
    
    return jsonify({'suggestions': sorted(list(keywords_set))})


@main.route('/all_keywords', methods=['GET'])
def all_keywords():
    from .db_utils import get_all_keywords  # zakładamy, że dodasz funkcję
    keywords = get_all_keywords()  # lista stringów: ["rescue", "friendship", ...]
    return jsonify(keywords)
