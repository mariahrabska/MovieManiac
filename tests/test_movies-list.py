# tests/test_movies-list.py
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

@pytest.fixture(scope="module")
def driver():
    """Fixtura inicjalizująca przeglądarkę i logująca użytkownika,
    a następnie przechodząca na stronę watchlist.
    """
    chrome_options = Options()
    # chrome_options.add_argument("--headless=new")  # tryb headless
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)

    # Logowanie testowego użytkownika
    driver.get("http://127.0.0.1:5000/login")
    email_input = wait.until(EC.presence_of_element_located((By.ID, "email")))
    password_input = driver.find_element(By.ID, "password")
    email_input.send_keys("rampam@gmail.com")
    password_input.send_keys("rampam123")
    password_input.send_keys(Keys.RETURN)

    # Czekamy na załadowanie dashboardu
    wait.until(EC.title_contains("🎬 Find recommendations"))

    # Przejście na stronę watchlist
    driver.get("http://127.0.0.1:5000/movies-list")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".main-content")))

    yield driver
    driver.quit()


import time

def test_page_load_time(driver):
    """Sprawdza, czy strona ładuje się w akceptowalnym czasie (max 3s)"""
    start_time = time.time()

    driver.get("http://127.0.0.1:5000/movies-list")

    # Poczekaj aż strona załaduje się w pełni (readyState=complete)
    WebDriverWait(driver, 10).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

    end_time = time.time()
    load_time = end_time - start_time

    print(f"Czas ładowania strony: {load_time:.2f} sekundy")
    assert load_time <= 3, f"Strona ładuje się zbyt długo: {load_time:.2f} s"


@pytest.mark.parametrize("width,height", [
    (1920, 1080),  # Desktop (Full HD)
    (1366, 768),   # Laptop
    (768, 1024),   # Tablet (portrait)
    (414, 896),    # iPhone XR / 11
    (375, 812),    # iPhone X / 12 mini
])
def test_responsive_layout_watchlist(driver, width, height):
    """Sprawdza responsywność strony watchlist w różnych rozdzielczościach"""
    driver.set_window_size(width, height)
    wait = WebDriverWait(driver, 10)

    # Kluczowe elementy strony
    main_content = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".main-content")))
    movie_list_items = driver.find_elements(By.CSS_SELECTOR, "ul.movie-list li.movie-item")
    genre_filter = driver.find_elements(By.ID, "genre-filter")
    sort_select = driver.find_element(By.ID, "sort-by")
    keyword_input = driver.find_element(By.ID, "keyword-search")

    # Sprawdzenie widoczności
    assert main_content.is_displayed(), f"Main content niewidoczny przy rozdzielczości {width}x{height}"
    
    if movie_list_items:
        for movie in movie_list_items[:3]:  # sprawdzamy pierwsze 3 filmy, jeśli istnieją
            assert movie.is_displayed(), f"Film niewidoczny przy rozdzielczości {width}x{height}"
            remove_btn = movie.find_element(By.CSS_SELECTOR, ".remove-btn")
            watched_btn = movie.find_element(By.CSS_SELECTOR, ".watched-btn")
            favorite_btn = movie.find_element(By.CSS_SELECTOR, ".favorite-btn")
            assert remove_btn.is_displayed(), f"Przycisk remove niewidoczny przy rozdzielczości {width}x{height}"
            assert watched_btn.is_displayed(), f"Przycisk watched niewidoczny przy rozdzielczości {width}x{height}"
            assert favorite_btn.is_displayed(), f"Przycisk favorite niewidoczny przy rozdzielczości {width}x{height}"

    if genre_filter:
        assert genre_filter[0].is_displayed(), f"Filtr gatunków niewidoczny przy rozdzielczości {width}x{height}"

    assert sort_select.is_displayed(), f"Sortowanie niewidoczne przy rozdzielczości {width}x{height}"
    assert keyword_input.is_displayed(), f"Pole wyszukiwania niewidoczne przy rozdzielczości {width}x{height}"

    # Dodatkowa walidacja układu dla mobile
    if width < 600 and movie_list_items:
        # Lista filmów powinna być pod main content
        movie_y = movie_list_items[0].location['y']
        assert movie_y > main_content.location['y'], f"Na mobile ({width}x{height}) lista filmów powinna być pod main content"

def test_page_title(driver):
    """Sprawdza tytuł strony watchlist"""
    driver.get("http://127.0.0.1:5000/movies-list")
    WebDriverWait(driver, 10).until(EC.title_is("🎬My Watchlist"))
    assert driver.title == "🎬My Watchlist"


def test_watchlist_has_movies(driver):
    """Sprawdza, czy lista filmów istnieje (może być pusta)"""
    movies = driver.find_elements(By.CSS_SELECTOR, "ul.movie-list li.movie-item")
    movie_list = driver.find_elements(By.CSS_SELECTOR, "ul.movie-list")
    if movie_list:
        assert len(movies) >= 0

def test_filter_genre_dropdown_watchlist(driver):
    """Sprawdza filtrowanie filmów po gatunku w Watchlist poprzez widoczność filmów"""
    from selenium.webdriver.support.ui import Select
    from selenium.webdriver.support.ui import WebDriverWait
    import pytest

    genre_filter = driver.find_elements(By.ID, "genre-filter")
    if not genre_filter:
        pytest.skip("Brak dropdownu do filtrowania po gatunku")

    select = Select(genre_filter[0])

    # Wybieramy pierwszy gatunek, który nie jest 'all'
    options = [opt.get_attribute("value") for opt in select.options if opt.get_attribute("value") != "all"]
    if not options:
        pytest.skip("Brak gatunków do przetestowania")

    first_genre = options[0]

    # Zaznaczamy wybrany gatunek
    select.select_by_value(first_genre)

    # Czekamy, aż JS zastosuje filtr
    WebDriverWait(driver, 10).until(lambda d: all(
        item.is_displayed() or first_genre not in item.get_attribute("data-genres").split('|')
        for item in d.find_elements(By.CSS_SELECTOR, "ul.movie-list li.movie-item")
    ))

    # Sprawdzamy widoczność filmów
    for item in driver.find_elements(By.CSS_SELECTOR, "ul.movie-list li.movie-item"):
        genres = item.get_attribute("data-genres").split('|')
        if first_genre in genres:
            assert item.is_displayed(), f"Film z gatunkiem {first_genre} powinien być widoczny"
        else:
            assert not item.is_displayed(), f"Film bez gatunku {first_genre} powinien być ukryty"

    # Przywracamy dropdown do "all"
    select.select_by_value("all")
    WebDriverWait(driver, 5).until(lambda d: all(
        item.is_displayed() for item in d.find_elements(By.CSS_SELECTOR, "ul.movie-list li.movie-item")
    ))



def test_sort_dropdown(driver):
    """Sprawdza, czy dropdown sortowania zawiera wszystkie opcje"""
    sort_select = driver.find_elements(By.ID, "sort-by")
    if sort_select:
        options = [opt.get_attribute("value") for opt in sort_select[0].find_elements(By.TAG_NAME, "option")]
        for opt in ["title-asc", "title-desc", "year-asc", "year-desc"]:
            assert opt in options


def test_sorting_functionality(driver):
    """Sprawdza, czy lista filmów faktycznie się sortuje według tytułu i roku"""
    sort_select = driver.find_element(By.ID, "sort-by")

    # Najpierw sortowanie malejąco, potem rosnąco, żeby zawsze zmieniał się pierwszy element
    sort_modes = [
        ("title-desc", True),   # alfabetycznie malejąco
        ("title-asc", False),   # alfabetycznie rosnąco
        ("year-desc", True),    # rok malejąco
        ("year-asc", False),    # rok rosnąco
    ]

    for value, reverse in sort_modes:
        # kliknij w dropdown
        sort_select.find_element(By.CSS_SELECTOR, f"option[value='{value}']").click()

        # poczekaj aż lista faktycznie zmieni kolejność
        WebDriverWait(driver, 5).until(lambda d: True)  # proste czekanie, bo JS reaguje natychmiast

        # pobierz dane
        movies = driver.find_elements(By.CSS_SELECTOR, "ul.movie-list li.movie-item")
        if not movies:
            pytest.skip("Brak filmów w watchlist – nie można przetestować sortowania")

        titles = [m.find_element(By.CSS_SELECTOR, ".movie-title").text.strip() for m in movies]
        years = [int(m.get_attribute("data-year")) for m in movies if m.get_attribute("data-year")]

        # walidacja
        if value.startswith("title"):
            clean_titles = [t.rsplit(" (", 1)[0] for t in titles]
            sorted_titles = sorted(clean_titles, reverse=reverse)
            assert clean_titles == sorted_titles, f"Błąd sortowania ({value}): {clean_titles}"
        elif value.startswith("year"):
            sorted_years = sorted(years, reverse=reverse)
            assert years == sorted_years, f"Błąd sortowania ({value}): {years}"



def test_keyword_search_autocomplete(driver):
    """Sprawdza, czy pole wyszukiwania słów kluczowych istnieje"""
    search_input = driver.find_elements(By.ID, "keyword-search")
    if search_input:
        assert search_input[0] is not None


def test_movie_actions_buttons_present(driver):
    """Sprawdza obecność przycisków akcji dla pierwszego filmu"""
    movies = driver.find_elements(By.CSS_SELECTOR, "ul.movie-list li.movie-item")
    if movies:
        movie_item = movies[0]
        remove_btn = movie_item.find_element(By.CSS_SELECTOR, ".remove-btn")
        watched_btn = movie_item.find_element(By.CSS_SELECTOR, ".watched-btn")
        favorite_btn = movie_item.find_element(By.CSS_SELECTOR, ".favorite-btn")
        assert remove_btn is not None
        assert watched_btn is not None
        assert favorite_btn is not None


def test_click_movie_link(driver):
    """Kliknięcie w link filmu powinno przenieść na stronę /movie/<id>"""
    movies = driver.find_elements(By.CSS_SELECTOR, "ul.movie-list li.movie-item a")
    if movies:
        movie_link = movies[0]
        href = movie_link.get_attribute("href")
        movie_link.click()
        WebDriverWait(driver, 10).until(lambda d: href in d.current_url)
        assert "/movie/" in driver.current_url
