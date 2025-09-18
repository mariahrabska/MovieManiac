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
