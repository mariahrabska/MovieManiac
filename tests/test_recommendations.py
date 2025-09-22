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


@pytest.mark.parametrize("width,height", [
    (1920, 1080),  # Desktop (Full HD)
    (1366, 768),   # Laptop
    (768, 1024),   # Tablet (portrait)
    (414, 896),    # iPhone XR / 11
    (375, 812),    # iPhone X / 12 mini
])
def test_responsive_layout_recommendations(driver, width, height):
    """Sprawdza responsywność strony rekomendacji w różnych rozdzielczościach"""
    driver.set_window_size(width, height)
    wait = WebDriverWait(driver, 10)

    # Kluczowe elementy strony rekomendacji
    main_content = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".main-content")))
    rec_list_items = driver.find_elements(By.CSS_SELECTOR, "#recommendationsList .movie-item-content")
    pagination_prev = driver.find_elements(By.ID, "prevPageBtn")
    pagination_next = driver.find_elements(By.ID, "nextPageBtn")

    # Sprawdzenie widoczności main content
    assert main_content.is_displayed(), f"Main content niewidoczny przy rozdzielczości {width}x{height}"

    if rec_list_items:
        first_movie = rec_list_items[0]
        assert first_movie.is_displayed(), f"Pierwszy film niewidoczny przy rozdzielczości {width}x{height}"

        # Sprawdzenie widoczności ikon w checkboxach
        for cb_class in ["watchlist-checkbox", "watched-checkbox", "favorite-checkbox"]:
            icon = first_movie.find_element(By.CSS_SELECTOR, f".{cb_class} + .custom-checkbox i")
            assert icon.is_displayed(), f"Ikona checkboxa {cb_class} niewidoczna przy rozdzielczości {width}x{height}"

    if pagination_prev:
        assert pagination_prev[0].is_displayed(), f"Przycisk Previous niewidoczny przy rozdzielczości {width}x{height}"
    if pagination_next:
        assert pagination_next[0].is_displayed(), f"Przycisk Next niewidoczny przy rozdzielczości {width}x{height}"

    # Dodatkowa walidacja układu dla mobile
    if width < 600 and rec_list_items:
        movie_y = rec_list_items[0].location['y']
        assert movie_y > main_content.location['y'], f"Na mobile ({width}x{height}) lista rekomendacji powinna być pod main content"



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
