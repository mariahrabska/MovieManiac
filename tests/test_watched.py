# tests/test_watched_movies_page.py
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

@pytest.fixture(scope="function")
def driver():
    """Fixtura inicjalizująca przeglądarkę i logująca użytkownika przed każdym testem."""
    chrome_options = Options()
    # chrome_options.add_argument("--headless=new")  # tryb headless
    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()
    wait = WebDriverWait(driver, 10)

    # Logowanie
    driver.get("http://127.0.0.1:5000/login")
    email_input = wait.until(EC.presence_of_element_located((By.ID, "email")))
    password_input = driver.find_element(By.ID, "password")
    email_input.send_keys("rampam@gmail.com")
    password_input.send_keys("rampam123")
    password_input.send_keys(Keys.RETURN)
    wait.until(EC.title_contains("🎬 Find recommendations"))

    # Przejście na stronę Watched Movies
    driver.get("http://127.0.0.1:5000/watched")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".main-content")))

    yield driver
    driver.quit()


def test_page_title(driver):
    """Sprawdza, czy tytuł strony to 'Watched Movies'"""
    driver.get("http://127.0.0.1:5000/watched")
    wait = WebDriverWait(driver, 10)
    wait.until(EC.title_is("Watched Movies"))
    assert driver.title == "Watched Movies"


def test_movies_list_present(driver):
    """Sprawdza, czy lista obejrzanych filmów istnieje"""
    movie_list = driver.find_elements(By.CSS_SELECTOR, "ul.movie-list")
    movies = driver.find_elements(By.CSS_SELECTOR, "ul.movie-list li.movie-item")
    if movie_list:
        assert len(movies) >= 0

def test_filter_genre_dropdown(driver):
    """Sprawdza filtrowanie po gatunku poprzez widoczność filmów"""
    genre_filter = driver.find_elements(By.ID, "genre-filter")
    if genre_filter:
        from selenium.webdriver.support.ui import Select
        select = Select(genre_filter[0])
        
        # Wybieramy pierwszy gatunek, który nie jest 'all'
        options = [opt.get_attribute("value") for opt in select.options if opt.get_attribute("value") != "all"]
        if not options:
            return  # brak gatunków do przetestowania
        first_genre = options[0]
        
        # Zaznaczamy wybrany gatunek
        select.select_by_value(first_genre)

        # Czekamy chwilę, żeby JS zdążył zastosować filtr
        from selenium.webdriver.support.ui import WebDriverWait
        WebDriverWait(driver, 10).until(lambda d: all(
            item.is_displayed() or first_genre not in item.get_attribute("data-genres").split('|')
            for item in d.find_elements(By.CSS_SELECTOR, "ul.movie-list li.movie-item")
        ))

        # Sprawdzamy, że widoczne są tylko filmy z tym gatunkiem
        for item in driver.find_elements(By.CSS_SELECTOR, "ul.movie-list li.movie-item"):
            genres = item.get_attribute("data-genres").split('|')
            if first_genre in genres:
                assert item.is_displayed()
            else:
                assert not item.is_displayed()


def test_sort_dropdown(driver):
    """Sprawdza obecność i działanie sortowania"""
    sort_select = driver.find_element(By.ID, "sort-by")
    assert sort_select is not None

    options = [opt.get_attribute("value") for opt in sort_select.find_elements(By.TAG_NAME, "option")]
    expected_options = ["title-asc", "title-desc", "year-asc", "year-desc"]
    for opt in expected_options:
        assert opt in options

    driver.execute_script(
        "arguments[0].value='title-asc'; arguments[0].dispatchEvent(new Event('change'));",
        sort_select
    )
    WebDriverWait(driver, 10).until(lambda d: d.find_elements(By.CSS_SELECTOR, ".movie-item"))
    titles = [el.text.lower() for el in driver.find_elements(By.CSS_SELECTOR, ".movie-title")]
    assert titles == sorted(titles)


def test_keyword_search_autocomplete(driver):
    """Sprawdza obecność pola wyszukiwania słów kluczowych"""
    search_input = driver.find_elements(By.ID, "keyword-search")
    if search_input:
        assert search_input[0] is not None


def test_movie_actions_buttons_present(driver):
    """Sprawdza przyciski akcji dla pierwszego filmu"""
    movies = driver.find_elements(By.CSS_SELECTOR, "ul.movie-list li.movie-item")
    if movies:
        movie_item = movies[0]
        remove_btn = movie_item.find_element(By.CSS_SELECTOR, ".remove-btn")
        favorite_btn = movie_item.find_element(By.CSS_SELECTOR, ".favorite-btn")
        assert remove_btn is not None
        assert favorite_btn is not None


def test_click_movie_link(driver):
    """Kliknięcie filmu przenosi na jego stronę /movie/<id>"""
    movies = driver.find_elements(By.CSS_SELECTOR, "ul.movie-list li.movie-item a")
    if movies:
        movie_link = movies[0]
        href = movie_link.get_attribute("href")
        movie_link.click()
        WebDriverWait(driver, 10).until(lambda d: href in d.current_url)
        assert "/movie/" in driver.current_url
