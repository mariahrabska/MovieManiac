# tests/test_dashboard.py
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


@pytest.fixture(scope="module")
def driver():
    """Fixtura inicjalizująca przeglądarkę i logująca użytkownika na czas testów"""
    chrome_options = Options()
    # chrome_options.add_argument("--headless=new")  # odkomentuj, jeśli chcesz tryb headless
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)

    # Otwieramy stronę logowania
    driver.get("http://127.0.0.1:5000/login")

    # Logowanie użytkownika testowego
    username_input = wait.until(EC.presence_of_element_located((By.ID, "email")))
    password_input = driver.find_element(By.ID, "password")

    username_input.send_keys("rampam@gmail.com")
    password_input.send_keys("rampam123")
    password_input.send_keys(Keys.RETURN)

    # Oczekiwanie na załadowanie dashboardu
    wait.until(EC.title_contains("🎬 Find recommendations"))

    yield driver  # udostępniamy driver testom

    driver.quit()  # zamknięcie przeglądarki po testach


def test_page_title(driver):
    """Sprawdza, czy tytuł strony zawiera poprawny tekst"""
    assert "🎬 Find recommendations" in driver.title


def test_movie_input_exists(driver):
    """Sprawdza, czy istnieje pole do wpisania tytułu filmu"""
    input_box = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "movie_title_input"))
    )
    assert input_box.is_displayed()


def test_submit_button_exists(driver):
    """Sprawdza, czy przycisk wyszukiwania rekomendacji istnieje i ma poprawny tekst"""
    button = driver.find_element(By.CSS_SELECTOR, "button.btn.btn-primary")
    assert button.is_displayed()
    assert button.text == "Show Recommendations"


def test_error_shown_for_invalid_movie(driver):
    """Sprawdza, czy po wpisaniu nieistniejącego filmu pojawia się komunikat błędu"""
    input_box = driver.find_element(By.ID, "movie_title_input")
    button = driver.find_element(By.CSS_SELECTOR, "button.btn.btn-primary")

    # Wpisanie nieistniejącego filmu
    input_box.clear()
    input_box.send_keys("Movie doesn't exist")
    button.click()

    # Sprawdź, czy komunikat błędu się pojawił
    error_div = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "movie_error"))
    )
    assert "❌ Please select a movie from the suggestions list" in error_div.text


def test_input_autocomplete_options(driver):
    """Sprawdza, czy po wpisaniu litery pojawiają się propozycje filmów (autocomplete)"""
    input_box = driver.find_element(By.ID, "movie_title_input")
    input_box.clear()
    input_box.send_keys("A")

    # Poczekaj aż pojawią się opcje w autocomplete
    WebDriverWait(driver, 10).until(
        lambda d: len(d.find_elements(By.CSS_SELECTOR, "#movie_titles option")) > 0
    )
    options = driver.find_elements(By.CSS_SELECTOR, "#movie_titles option")
    assert len(options) > 0
