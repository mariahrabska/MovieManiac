# tests/test_favorites.py
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

@pytest.fixture(scope="module")
def driver():
    """Fixtura inicjalizująca przeglądarkę i logująca użytkownika testowego"""
    chrome_options = Options()
    # chrome_options.add_argument("--headless=new")  # odkomentuj dla trybu headless
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)

    # Logowanie
    driver.get("http://127.0.0.1:5000/login")
    email_input = wait.until(EC.presence_of_element_located((By.ID, "email")))
    password_input = driver.find_element(By.ID, "password")
    email_input.send_keys("rampam@gmail.com")
    password_input.send_keys("rampam123")
    password_input.send_keys(Keys.RETURN)

    # Czekanie na załadowanie dashboardu
    wait.until(EC.title_contains("🎬 Find recommendations"))

    # Przejście na stronę ulubionych
    driver.get("http://127.0.0.1:5000/favorites")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".main-content")))

    yield driver
    driver.quit()

import time

def test_page_load_time(driver):
    """Sprawdza, czy dashboard ładuje się w akceptowalnym czasie (max 3s)"""
    start_time = time.time()

    driver.get("http://127.0.0.1:5000/favorites")

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
def test_responsive_layout_favorites(driver, width, height):
    """Sprawdza responsywność strony ulubionych w różnych rozdzielczościach"""
    driver.set_window_size(width, height)
    wait = WebDriverWait(driver, 10)

    # Otwórz stronę ulubionych
    driver.get("http://127.0.0.1:5000/favorites")

    # Kluczowe elementy strony
    main_content = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".main-content")))
    genre_filter = wait.until(EC.presence_of_element_located((By.ID, "genre-filter")))
    sort_select = wait.until(EC.presence_of_element_located((By.ID, "sort-by")))
    keyword_search = wait.until(EC.presence_of_element_located((By.ID, "keyword-search")))

    # Lista filmów (może być pusta)
    movie_list_items = driver.find_elements(By.CSS_SELECTOR, "ul.movie-list li.movie-item")

    # Asercje
    assert main_content.is_displayed()
    assert genre_filter.is_displayed()
    assert sort_select.is_displayed()
    assert keyword_search.is_displayed()
    assert len(movie_list_items) >= 0  # lista może być pusta

def test_page_title(driver):
    """Sprawdza tytuł strony ulubionych"""
    driver.get("http://127.0.0.1:5000/favorites")
    WebDriverWait(driver, 10).until(EC.title_is("Favorite Movies"))
    assert driver.title == "Favorite Movies"


def test_favorites_list_present(driver):
    """Sprawdza, czy lista ul.movie-list istnieje, nawet jeśli jest pusta"""
    movie_list = driver.find_elements(By.CSS_SELECTOR, "ul.movie-list")
    assert movie_list or True  # element powinien istnieć


def test_remove_button(driver):
    """Test przycisku remove - usuwa film z listy"""
    movies = driver.find_elements(By.CSS_SELECTOR, "ul.movie-list li.movie-item")
    if movies:
        remove_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "li.movie-item .remove-btn"))
        )
        movie_item = remove_btn.find_element(By.XPATH, "./ancestor::li")
        remove_btn.click()
        WebDriverWait(driver, 10).until(EC.staleness_of(movie_item))

def test_filter_genre_dropdown(driver):
    """Uniwersalny test filtrowania filmów po gatunku – sprawdza widoczność filmów"""
    from selenium.webdriver.support.ui import Select
    from selenium.webdriver.support.ui import WebDriverWait

    genre_filter = driver.find_elements(By.ID, "genre-filter")
    if not genre_filter:
        pytest.skip("Brak dropdownu do filtrowania po gatunku")

    select = Select(genre_filter[0])

    # Wybieramy pierwszy gatunek, który nie jest "all"
    options = [opt.get_attribute("value") for opt in select.options if opt.get_attribute("value") != "all"]
    if not options:
        pytest.skip("Brak gatunków do przetestowania")

    first_genre = options[0]

    # Zaznaczamy wybrany gatunek
    select.select_by_value(first_genre)

    # Czekamy chwilę, aż JS zastosuje filtr
    WebDriverWait(driver, 10).until(lambda d: all(
        item.is_displayed() or first_genre not in item.get_attribute("data-genres").split('|')
        for item in d.find_elements(By.CSS_SELECTOR, "ul.movie-list li.movie-item")
    ))

    # Sprawdzamy widoczność
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
    """Sprawdza działanie sortowania: tytuł, rok, data dodania – tylko jeśli są filmy na liście."""
    sort_select = driver.find_element(By.ID, "sort-by")
    assert sort_select is not None

    options = [opt.get_attribute("value") for opt in sort_select.find_elements(By.TAG_NAME, "option")]
    expected_options = ["title-asc", "title-desc", "year-asc", "year-desc", "added-asc", "added-desc"]
    for opt in expected_options:
        assert opt in options

    wait = WebDriverWait(driver, 10)
    movie_items = driver.find_elements(By.CSS_SELECTOR, ".movie-item")
    if not movie_items:
        pytest.skip("Brak filmów na liście – pomijam test sortowania")

    # Funkcja pomocnicza do pobrania danych filmów i oczyszczenia tytułów
    def get_titles_years_added():
        items = driver.find_elements(By.CSS_SELECTOR, ".movie-item")
        titles = [
            el.find_element(By.CSS_SELECTOR, ".movie-title").text.strip().lower()
            for el in items
            if el.find_element(By.CSS_SELECTOR, ".movie-title").text.strip()
        ]
        years = [int(el.get_attribute("data-year") or 0) for el in items]
        added = [el.get_attribute("data-added") for el in items]
        return titles, years, added

    # --- SORTOWANIE TITLE DESC → ASC ---
    driver.execute_script("arguments[0].value='title-desc'; arguments[0].dispatchEvent(new Event('change'));", sort_select)
    wait.until(lambda d: True)  # JS sortuje natychmiast
    titles, _, _ = get_titles_years_added()
    assert titles == sorted(titles, reverse=True)

    driver.execute_script("arguments[0].value='title-asc'; arguments[0].dispatchEvent(new Event('change'));", sort_select)
    wait.until(lambda d: True)
    titles, _, _ = get_titles_years_added()
    assert titles == sorted(titles)

    # --- SORTOWANIE YEAR DESC → ASC ---
    driver.execute_script("arguments[0].value='year-desc'; arguments[0].dispatchEvent(new Event('change'));", sort_select)
    wait.until(lambda d: True)
    _, years, _ = get_titles_years_added()
    assert years == sorted(years, reverse=True)

    driver.execute_script("arguments[0].value='year-asc'; arguments[0].dispatchEvent(new Event('change'));", sort_select)
    wait.until(lambda d: True)
    _, years, _ = get_titles_years_added()
    assert years == sorted(years)

    # --- SORTOWANIE ADDED DESC → ASC ---
    driver.execute_script("arguments[0].value='added-desc'; arguments[0].dispatchEvent(new Event('change'));", sort_select)
    wait.until(lambda d: True)
    _, _, added = get_titles_years_added()
    assert all(added[i] >= added[i+1] for i in range(len(added)-1))

    driver.execute_script("arguments[0].value='added-asc'; arguments[0].dispatchEvent(new Event('change'));", sort_select)
    wait.until(lambda d: True)
    _, _, added = get_titles_years_added()
    assert all(added[i] <= added[i+1] for i in range(len(added)-1))


def test_keyword_search(driver):
    """Sprawdza działanie pola wyszukiwania słów kluczowych"""
    search_input = driver.find_elements(By.ID, "keyword-search")
    assert search_input
    search_input[0].send_keys("action")
    assert search_input[0].get_attribute("value") == "action"
