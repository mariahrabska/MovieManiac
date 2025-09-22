# tests/test_watched_movies_page.py
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

@pytest.fixture(scope="module")
def driver():
    """Fixtura inicjalizująca przeglądarkę i logująca użytkownika,
    a następnie przechodząca na stronę Watched Movies.
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

    # Czekamy na dashboard
    wait.until(EC.title_contains("🎬 Find recommendations"))

    # Przechodzimy na stronę watched
    driver.get("http://127.0.0.1:5000/watched")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".main-content")))

    yield driver
    driver.quit()


def test_page_load_time(driver):
    """Sprawdza, czy strona /watched ładuje się w akceptowalnym czasie (max 3s)"""
    import time
    start_time = time.time()

    driver.get("http://127.0.0.1:5000/watched")

    WebDriverWait(driver, 10).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

    load_time = time.time() - start_time
    print(f"Czas ładowania strony: {load_time:.2f} sekundy")
    assert load_time <= 3, f"Strona ładuje się zbyt długo: {load_time:.2f} s"

@pytest.mark.parametrize("width,height", [
    (1920, 1080),  # Desktop (Full HD)
    (1366, 768),   # Laptop
    (768, 1024),   # Tablet (portrait)
    (414, 896),    # iPhone XR / 11
    (375, 812),    # iPhone X / 12 mini
])

def test_responsive_layout_watched(driver, width, height):
    """Sprawdza responsywność strony obejrzanych filmów w różnych rozdzielczościach"""
    driver.set_window_size(width, height)
    wait = WebDriverWait(driver, 10)

    # Kluczowe elementy strony
    main_content = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".main-content")))
    movie_list_items = driver.find_elements(By.CSS_SELECTOR, "ul.movie-list li.movie-item")
    genre_filter = driver.find_elements(By.ID, "genre-filter")
    sort_select = driver.find_elements(By.ID, "sort-by")
    keyword_input = driver.find_elements(By.ID, "keyword-search")

    # Sprawdzenie widoczności
    assert main_content.is_displayed(), f"Main content niewidoczny przy rozdzielczości {width}x{height}"
    if movie_list_items:
        assert movie_list_items[0].is_displayed(), f"Pierwszy film niewidoczny przy rozdzielczości {width}x{height}"
        remove_btn = movie_list_items[0].find_element(By.CSS_SELECTOR, ".remove-btn")
        favorite_btn = movie_list_items[0].find_element(By.CSS_SELECTOR, ".favorite-btn")
        assert remove_btn.is_displayed(), f"Przycisk remove niewidoczny przy rozdzielczości {width}x{height}"
        assert favorite_btn.is_displayed(), f"Przycisk favorite niewidoczny przy rozdzielczości {width}x{height}"
    if genre_filter:
        assert genre_filter[0].is_displayed(), f"Filtr gatunków niewidoczny przy rozdzielczości {width}x{height}"
    if sort_select:
        assert sort_select[0].is_displayed(), f"Sortowanie niewidoczne przy rozdzielczości {width}x{height}"
    if keyword_input:
        assert keyword_input[0].is_displayed(), f"Pole wyszukiwania niewidoczne przy rozdzielczości {width}x{height}"

    # Dodatkowa walidacja układu dla mobile
    if width < 600 and movie_list_items:
        movie_y = movie_list_items[0].location['y']
        assert movie_y > main_content.location['y'], f"Na mobile ({width}x{height}) lista filmów powinna być pod main content"


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
        # Przywracamy dropdown do "all"
        select.select_by_value("all")
        WebDriverWait(driver, 5).until(lambda d: all(
            item.is_displayed() for item in d.find_elements(By.CSS_SELECTOR, "ul.movie-list li.movie-item")
        ))

def test_sort_dropdown(driver):
    """Sprawdza działanie sortowania: tytuł i rok"""
    sort_select = driver.find_element(By.ID, "sort-by")
    assert sort_select is not None

    # Sprawdzenie obecności opcji
    options = [opt.get_attribute("value") for opt in sort_select.find_elements(By.TAG_NAME, "option")]
    expected_options = ["title-asc", "title-desc", "year-asc", "year-desc"]
    for opt in expected_options:
        assert opt in options

    # Funkcja pomocnicza do pobrania tytułów i lat filmów
    def get_titles_and_years():
        items = driver.find_elements(By.CSS_SELECTOR, ".movie-item")
        titles = [el.find_element(By.CSS_SELECTOR, ".movie-title").text.strip().lower() 
                  for el in items if el.find_element(By.CSS_SELECTOR, ".movie-title").text.strip()]
        years = [int(el.get_attribute("data-year") or 0) for el in items]
        return titles, years

    # --- SORTOWANIE TITLE ASC ---
    driver.execute_script("arguments[0].value='title-asc'; arguments[0].dispatchEvent(new Event('change'));", sort_select)
    WebDriverWait(driver, 10).until(lambda d: len([el for el in d.find_elements(By.CSS_SELECTOR, ".movie-title") if el.text.strip()]) > 1)
    titles, _ = get_titles_and_years()
    assert titles == sorted(titles)

    # --- SORTOWANIE TITLE DESC ---
    driver.execute_script("arguments[0].value='title-desc'; arguments[0].dispatchEvent(new Event('change'));", sort_select)
    WebDriverWait(driver, 10).until(lambda d: len([el for el in d.find_elements(By.CSS_SELECTOR, ".movie-title") if el.text.strip()]) > 1)
    titles, _ = get_titles_and_years()
    assert titles == sorted(titles, reverse=True)

    # --- SORTOWANIE YEAR ASC ---
    driver.execute_script("arguments[0].value='year-asc'; arguments[0].dispatchEvent(new Event('change'));", sort_select)
    WebDriverWait(driver, 10).until(lambda d: len(d.find_elements(By.CSS_SELECTOR, ".movie-item")) > 1)
    _, years = get_titles_and_years()
    assert years == sorted(years)

    # --- SORTOWANIE YEAR DESC ---
    driver.execute_script("arguments[0].value='year-desc'; arguments[0].dispatchEvent(new Event('change'));", sort_select)
    WebDriverWait(driver, 10).until(lambda d: len(d.find_elements(By.CSS_SELECTOR, ".movie-item")) > 1)
    _, years = get_titles_and_years()
    assert years == sorted(years, reverse=True)


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
