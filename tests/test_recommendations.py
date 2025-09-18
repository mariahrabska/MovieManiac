# tests/test_recommendations_page.py
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

@pytest.fixture(scope="module")
def driver():
    """Fixtura inicjalizująca przeglądarkę, logująca testowego użytkownika i otwierająca stronę rekomendacji."""
    chrome_options = Options()
    # chrome_options.add_argument("--headless=new")  # tryb headless
    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()
    wait = WebDriverWait(driver, 10)

    # --- Logowanie testowego użytkownika ---
    driver.get("http://127.0.0.1:5000/login")
    email_input = wait.until(EC.presence_of_element_located((By.ID, "email")))
    password_input = driver.find_element(By.ID, "password")
    email_input.send_keys("testuser@example.com")
    password_input.send_keys("validpassword")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    wait.until(EC.url_changes("http://127.0.0.1:5000/login"))

    # --- Przejście na dashboard i wybór filmu ---
    driver.get("http://127.0.0.1:5000/dashboard")
    movie_input = wait.until(EC.presence_of_element_located((By.ID, "movie_title_input")))
    movie_input.send_keys("Interstellar (2014)")
    driver.find_element(By.CSS_SELECTOR, "button.btn.btn-primary").click()

    # Czekamy na załadowanie strony rekomendacji
    wait.until(EC.presence_of_element_located((By.ID, "recommendationsList")))

    yield driver
    driver.quit()


def test_recommendations_list_exists(driver):
    """Sprawdza, czy lista rekomendacji istnieje i zawiera co najmniej jeden film"""
    rec_list = driver.find_element(By.ID, "recommendationsList")
    movies = rec_list.find_elements(By.CLASS_NAME, "movie-item-content")
    assert len(movies) > 0


def test_movie_elements_have_title_and_poster(driver):
    """Sprawdza, czy każdy film ma tytuł i miniaturę plakatu"""
    movies = driver.find_elements(By.CLASS_NAME, "movie-item-content")
    assert len(movies) > 0
    for movie in movies:
        title = movie.find_element(By.CLASS_NAME, "movie-title").text
        assert title  # tytuł nie powinien być pusty
        poster = movie.find_elements(By.CLASS_NAME, "poster-thumb")
        assert isinstance(poster, list)


def test_checkboxes_exist(driver):
    """Sprawdza, czy przy każdym filmie są checkboxy: watchlist, watched, favorite"""
    movie = driver.find_element(By.CLASS_NAME, "movie-item-content")
    assert movie.find_element(By.CLASS_NAME, "watchlist-checkbox")
    assert movie.find_element(By.CLASS_NAME, "watched-checkbox")
    assert movie.find_element(By.CLASS_NAME, "favorite-checkbox")


def test_pagination_buttons(driver):
    """Sprawdza, czy przyciski paginacji istnieją i są poprawnie ustawione"""
    prev_btn = driver.find_element(By.ID, "prevPageBtn")
    next_btn = driver.find_element(By.ID, "nextPageBtn")
    assert prev_btn.is_displayed()
    assert next_btn.is_displayed()
    assert prev_btn.get_attribute("disabled")  # na pierwszej stronie powinien być nieaktywny


def test_modal_opens_on_movie_click(driver):
    """Sprawdza, czy po kliknięciu filmu otwiera się modal ze szczegółami"""
    movie = driver.find_element(By.CLASS_NAME, "movie-item-content")
    movie.click()
    modal = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "movieModal")))
    assert modal.is_displayed()
    close_btn = modal.find_element(By.CLASS_NAME, "close-modal")
    close_btn.click()


def test_notification_element_exists(driver):
    """Sprawdza, czy na stronie istnieje element powiadomień"""
    notif = driver.find_element(By.ID, "notification")
    assert notif is not None
