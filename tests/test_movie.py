# tests/test_movie.py
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

@pytest.fixture(scope="module")
def driver():
    """Fixtura inicjalizująca przeglądarkę i logująca testowego użytkownika,
    a następnie przechodząca na stronę konkretnego filmu.
    """
    chrome_options = Options()
    # chrome_options.add_argument("--headless=new")  # tryb headless (bez okna przeglądarki)
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)

    # --- Logowanie ---
    driver.get("http://127.0.0.1:5000/login")
    email_input = wait.until(EC.presence_of_element_located((By.ID, "email")))
    password_input = driver.find_element(By.ID, "password")
    email_input.send_keys("rampam@gmail.com")
    password_input.send_keys("rampam123")
    password_input.send_keys(Keys.RETURN)

    # Czekamy, aż dashboard się załaduje
    wait.until(EC.title_contains("🎬 Find recommendations"))

    # --- Przejście na stronę filmu ---
    driver.get("http://127.0.0.1:5000/movie/1")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.movie-details")))

    yield driver
    driver.quit()


@pytest.mark.parametrize("width,height", [
    (1920, 1080),  # Desktop (Full HD)
    (1366, 768),   # Laptop
    (768, 1024),   # Tablet (portrait)
    (414, 896),    # iPhone XR / 11
    (375, 812),    # iPhone X / 12 mini
])
def test_responsive_layout_movie(driver, width, height):
    """Sprawdza responsywność strony filmu w różnych rozdzielczościach"""
    driver.set_window_size(width, height)
    wait = WebDriverWait(driver, 10)

    # Kluczowe elementy strony filmu
    poster = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "img.poster-thumb")))
    title = driver.find_element(By.CSS_SELECTOR, "div.movie-main-info h1")
    rating = driver.find_element(By.CSS_SELECTOR, "div.movie-main-info p")
    overview = driver.find_element(By.CSS_SELECTOR, "div.movie-main-info p:nth-of-type(2)")
    additional_info_items = driver.find_elements(By.CSS_SELECTOR, "div.movie-additional-info ul li")

    # Sprawdzenie widoczności
    assert poster.is_displayed(), f"Plakat niewidoczny przy rozdzielczości {width}x{height}"
    assert title.is_displayed(), f"Tytuł niewidoczny przy rozdzielczości {width}x{height}"
    assert rating.is_displayed(), f"Ocena niewidoczna przy rozdzielczości {width}x{height}"
    assert overview.is_displayed(), f"Opis filmu niewidoczny przy rozdzielczości {width}x{height}"
    assert len(additional_info_items) > 0, f"Dodatkowe informacje niewidoczne przy rozdzielczości {width}x{height}"

    # Dodatkowa walidacja układu dla mobile
    if width < 600:
        # Sprawdzenie, że plakat jest nad tytułem i info (typowy układ mobilny)
        poster_y = poster.location['y']
        title_y = title.location['y']
        assert poster_y < title_y, f"Na mobile ({width}x{height}) plakat powinien być nad tytułem"

def test_page_title_contains_movie_title(driver):
    """Sprawdza, czy tytuł strony zawiera ikonę 🎬"""
    title = driver.title
    assert "🎬" in title


def test_movie_main_elements_exist(driver):
    """Sprawdza, czy główne elementy strony filmu istnieją:
    - plakat
    - tytuł
    - tagline (opcjonalny)
    - ocena (gwiazdki)
    - opis filmu
    """
    # Plakat
    poster = driver.find_elements(By.CSS_SELECTOR, "img.poster-thumb")
    assert isinstance(poster, list)

    # Tytuł (h1)
    h1 = driver.find_element(By.CSS_SELECTOR, "div.movie-main-info h1")
    assert len(h1.text) > 0

    # Tagline (opcjonalny)
    tagline = driver.find_elements(By.CSS_SELECTOR, "div.movie-main-info h3 em")
    if tagline:
        assert len(tagline[0].text) > 0

    # Ocena
    rating = driver.find_element(By.CSS_SELECTOR, "div.movie-main-info p")
    assert "⭐" in rating.text

    # Opis filmu
    overview = driver.find_element(By.CSS_SELECTOR, "div.movie-main-info p:nth-of-type(2)")
    assert len(overview.text) > 0


def test_additional_info_exists(driver):
    """Sprawdza wyświetlanie dodatkowych informacji o filmie
    (Status, Data premiery)
    """
    info_items = driver.find_elements(By.CSS_SELECTOR, "div.movie-additional-info ul li")
    assert len(info_items) > 0  # musi być co najmniej jeden element
    texts = [li.text for li in info_items]
    assert any("Status" in t for t in texts)
    assert any("Release Date" in t for t in texts)
