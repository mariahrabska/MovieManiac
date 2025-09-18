# tests/test_ranking_page.py
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

@pytest.fixture(scope="module")
def driver():
    """Fixtura inicjalizująca przeglądarkę, logująca użytkownika i otwierająca stronę ranking."""
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

    # Przejście na stronę ranking
    driver.get("http://127.0.0.1:5000/ranking")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".main-content")))

    yield driver
    driver.quit()


def test_page_title(driver):
    """Sprawdza tytuł strony rankingowej"""
    assert driver.title == "🎬Movie Ranking"


def test_ranking_list_present(driver):
    """Lista rankingowa powinna istnieć"""
    ranking_list = driver.find_elements(By.CSS_SELECTOR, "ul.ranking-list")
    assert len(ranking_list) > 0


def test_ranking_items_present(driver):
    """Lista rankingowa powinna zawierać elementy"""
    items = driver.find_elements(By.CSS_SELECTOR, "ul.ranking-list li.ranking-item")
    assert len(items) > 0


def test_movie_links(driver):
    """Kliknięcie filmu przekierowuje na jego stronę /movie/<id>"""
    movie_links = driver.find_elements(By.CSS_SELECTOR, "ul.ranking-list li.ranking-item a")
    if movie_links:
        href = movie_links[0].get_attribute("href")
        movie_links[0].click()
        WebDriverWait(driver, 10).until(lambda d: href in d.current_url)
        assert "/movie/" in driver.current_url
        # wracamy do strony ranking, aby inne testy działały
        driver.back()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".main-content")))


def test_movie_info_present(driver):
    """Sprawdza obecność informacji o filmie: tytuł, ocena, gatunki, opis"""
    items = driver.find_elements(By.CSS_SELECTOR, "ul.ranking-list li.ranking-item")
    if items:
        info = items[0].find_element(By.CSS_SELECTOR, ".movie-info")
        title = info.find_element(By.CSS_SELECTOR, ".movie-title")
        vote = info.find_element(By.CSS_SELECTOR, ".vote-average")
        genres = info.find_element(By.CSS_SELECTOR, ".movie-genres")
        desc = info.find_element(By.CSS_SELECTOR, ".movie-description")
        assert title is not None
        assert vote is not None
        assert genres is not None
        assert desc is not None


def test_pagination_next(driver):
    """Sprawdza obecność przycisku Next w paginacji"""
    next_btn = driver.find_elements(By.CSS_SELECTOR, ".pagination a[href*='page=']")
    assert any("Next" in btn.text for btn in next_btn)


def test_pagination_previous(driver):
    """Sprawdza obecność przycisku Previous w paginacji (jeśli strona >1)"""
    prev_btn = driver.find_elements(By.CSS_SELECTOR, ".pagination a")
    if len(prev_btn) > 1:
        assert any("Previous" in btn.text for btn in prev_btn)
