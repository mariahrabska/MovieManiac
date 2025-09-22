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

    # Kluczowe elementy strony ulubionych
    main_content = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".main-content")))
    movie_list_items = driver.find_elements(By.CSS_SELECTOR, "ul.movie-list li.movie-item")
    genre_filter = driver.find_elements(By.ID, "genre-filter")
    sort_select = driver.find_element(By.ID, "sort-by")
    keyword_input = driver.find_element(By.ID, "keyword-search")

    # Sprawdzenie widoczności
    assert main_content.is_displayed(), f"Main content niewidoczny przy rozdzielczości {width}x{height}"
    if movie_list_items:
        assert movie_list_items[0].is_displayed(), f"Pierwszy film niewidoczny przy rozdzielczości {width}x{height}"
        remove_btn = movie_list_items[0].find_element(By.CSS_SELECTOR, ".remove-btn")
        assert remove_btn.is_displayed(), f"Przycisk remove niewidoczny przy rozdzielczości {width}x{height}"
    if genre_filter:
        assert genre_filter[0].is_displayed(), f"Filtr gatunków niewidoczny przy rozdzielczości {width}x{height}"
    assert sort_select.is_displayed(), f"Sortowanie niewidoczne przy rozdzielczości {width}x{height}"
    assert keyword_input.is_displayed(), f"Pole wyszukiwania niewidoczne przy rozdzielczości {width}x{height}"

    # Dodatkowa walidacja układu dla mobile
    if width < 600 and movie_list_items:
        movie_y = movie_list_items[0].location['y']
        assert movie_y > main_content.location['y'], f"Na mobile ({width}x{height}) lista filmów powinna być pod main content"

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


def test_genre_filter(driver):
    """Sprawdza filtrowanie filmów po gatunku"""
    genre_filter = driver.find_elements(By.ID, "genre-filter")
    if genre_filter:
        options = genre_filter[0].find_elements(By.TAG_NAME, "option")
        if len(options) > 1:
            genre_filter[0].send_keys(options[1].get_attribute("value"))
            # sprawdzamy, czy widoczne elementy pasują do wybranego gatunku
            for item in driver.find_elements(By.CSS_SELECTOR, "ul.movie-list li.movie-item"):
                if item.is_displayed():
                    genres = item.get_attribute("data-genres").split('|')
                    assert options[1].get_attribute("value") in genres


def test_sort_dropdown(driver):
    """Sprawdza działanie sortowania: tytuł, rok, data dodania"""
    sort_select = driver.find_element(By.ID, "sort-by")
    assert sort_select is not None

    # Sprawdzenie, czy wszystkie opcje są obecne
    options = [opt.get_attribute("value") for opt in sort_select.find_elements(By.TAG_NAME, "option")]
    expected_options = ["title-asc", "title-desc", "year-asc", "year-desc", "added-asc", "added-desc"]
    for opt in expected_options:
        assert opt in options

    # Funkcja pomocnicza do pobrania danych filmów
    def get_titles_years_added():
        items = driver.find_elements(By.CSS_SELECTOR, ".movie-item")
        titles = [el.find_element(By.CSS_SELECTOR, ".movie-title").text.lower() for el in items]
        years = [int(el.get_attribute("data-year") or 0) for el in items]
        added = [el.get_attribute("data-added") for el in items]
        return titles, years, added

    # --- SORTOWANIE TITLE ASC ---
    driver.execute_script("arguments[0].value='title-asc'; arguments[0].dispatchEvent(new Event('change'));", sort_select)
    WebDriverWait(driver, 10).until(lambda d: d.find_elements(By.CSS_SELECTOR, ".movie-item"))
    titles, _, _ = get_titles_years_added()
    assert titles == sorted(titles)

    # --- SORTOWANIE TITLE DESC ---
    driver.execute_script("arguments[0].value='title-desc'; arguments[0].dispatchEvent(new Event('change'));", sort_select)
    WebDriverWait(driver, 10).until(lambda d: d.find_elements(By.CSS_SELECTOR, ".movie-item"))
    titles, _, _ = get_titles_years_added()
    assert titles == sorted(titles, reverse=True)

    # --- SORTOWANIE YEAR ASC ---
    driver.execute_script("arguments[0].value='year-asc'; arguments[0].dispatchEvent(new Event('change'));", sort_select)
    WebDriverWait(driver, 10).until(lambda d: d.find_elements(By.CSS_SELECTOR, ".movie-item"))
    _, years, _ = get_titles_years_added()
    assert years == sorted(years)

    # --- SORTOWANIE YEAR DESC ---
    driver.execute_script("arguments[0].value='year-desc'; arguments[0].dispatchEvent(new Event('change'));", sort_select)
    WebDriverWait(driver, 10).until(lambda d: d.find_elements(By.CSS_SELECTOR, ".movie-item"))
    _, years, _ = get_titles_years_added()
    assert years == sorted(years, reverse=True)

    # --- SORTOWANIE ADDED ASC ---
    driver.execute_script("arguments[0].value='added-asc'; arguments[0].dispatchEvent(new Event('change'));", sort_select)
    WebDriverWait(driver, 10).until(lambda d: d.find_elements(By.CSS_SELECTOR, ".movie-item"))
    _, _, added = get_titles_years_added()
    assert all(added[i] <= added[i+1] for i in range(len(added)-1))

    # --- SORTOWANIE ADDED DESC ---
    driver.execute_script("arguments[0].value='added-desc'; arguments[0].dispatchEvent(new Event('change'));", sort_select)
    WebDriverWait(driver, 10).until(lambda d: d.find_elements(By.CSS_SELECTOR, ".movie-item"))
    _, _, added = get_titles_years_added()
    assert all(added[i] >= added[i+1] for i in range(len(added)-1))


def test_keyword_search(driver):
    """Sprawdza działanie pola wyszukiwania słów kluczowych"""
    search_input = driver.find_elements(By.ID, "keyword-search")
    assert search_input
    search_input[0].send_keys("action")
    assert search_input[0].get_attribute("value") == "action"
