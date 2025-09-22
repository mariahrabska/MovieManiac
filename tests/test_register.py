# tests/test_register.py
import pytest
import random
import string
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException


@pytest.fixture(scope="module")
def driver():
    """Fixtura inicjalizująca przeglądarkę na czas testów"""
    options = Options()
    options.add_argument("--headless")  # tryb headless (bez okienka)
    service = Service()
    driver = webdriver.Chrome(service=service, options=options)
    driver.delete_all_cookies()
    yield driver
    driver.quit()  # sprzątanie po wszystkich testach


@pytest.fixture(autouse=True)
def open_register_page(driver):
    """Fixtura automatycznie uruchamiana przed każdym testem.
    Otwiera stronę rejestracji i czeka aż się załaduje.
    """
    driver.get("http://127.0.0.1:5000/register")
    WebDriverWait(driver, 10).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )


def get_flashes(driver):
    """Pomocnicza funkcja pobierająca flash messages z DOM (maks. 5s czekania)."""
    try:
        flashes = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul.flashes li"))
        )
    except TimeoutException:
        flashes = []
    return flashes


# --- TESTY ---

import time

def test_page_load_time(driver):
    """Sprawdza, czy strona ładuje się w akceptowalnym czasie (max 3s)"""
    start_time = time.time()

    driver.get("http://127.0.0.1:5000/register")

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
def test_responsive_layout_register(driver, width, height):
    """Sprawdza responsywność strony rejestracji w różnych rozdzielczościach"""
    driver.set_window_size(width, height)
    wait = WebDriverWait(driver, 10)

    # Kluczowe elementy formularza
    username_input = wait.until(EC.presence_of_element_located((By.ID, "username")))
    email_input = driver.find_element(By.ID, "email")
    password_input = driver.find_element(By.ID, "password")
    toggle_btn = driver.find_element(By.ID, "togglePassword")
    register_btn = driver.find_element(By.CSS_SELECTOR, "button.btn-register")

    # Sprawdzenie widoczności
    assert username_input.is_displayed(), f"Pole username niewidoczne przy rozdzielczości {width}x{height}"
    assert email_input.is_displayed(), f"Pole email niewidoczne przy rozdzielczości {width}x{height}"
    assert password_input.is_displayed(), f"Pole hasła niewidoczne przy rozdzielczości {width}x{height}"
    assert toggle_btn.is_displayed(), f"Przycisk pokaż/ukryj hasło niewidoczny przy rozdzielczości {width}x{height}"
    assert register_btn.is_displayed(), f"Przycisk rejestracji niewidoczny przy rozdzielczości {width}x{height}"

    # Dodatkowa walidacja układu dla mobile
    if width < 600:
        assert register_btn.location['y'] > password_input.location['y'], (
            f"Na mobile ({width}x{height}) przycisk rejestracji nie znajduje się pod polem hasła"
        )


def test_page_title(driver):
    """Sprawdza, czy tytuł strony rejestracji jest poprawny"""
    assert "⚡ MovieManiac: Register" in driver.title


def test_input_fields_exist(driver):
    """Sprawdza, czy istnieją wszystkie wymagane pola formularza"""
    username = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "username"))
    )
    email = driver.find_element(By.ID, "email")
    password = driver.find_element(By.ID, "password")
    assert username is not None
    assert email is not None
    assert password is not None


def test_submit_button_exists(driver):
    """Sprawdza, czy przycisk rejestracji jest obecny"""
    button = driver.find_element(By.CSS_SELECTOR, "button.btn-register")
    assert button is not None


def test_invalid_email_shows_error(driver):
    """Sprawdza walidację JS dla błędnego e-maila"""
    username_input = driver.find_element(By.ID, "username")
    email_input = driver.find_element(By.ID, "email")
    password_input = driver.find_element(By.ID, "password")
    form = driver.find_element(By.CSS_SELECTOR, "form.register-form")

    username_input.send_keys("testuser")
    email_input.send_keys("invalidemail")  # niepoprawny adres
    password_input.send_keys("password123")

    # submit przez JS (symuluje kliknięcie submit)
    driver.execute_script("arguments[0].submit();", form)

    flashes = get_flashes(driver)
    assert any('Email has to contain "@" and "."' in f.text for f in flashes)


def test_short_password_shows_error(driver):
    """Sprawdza walidację długości hasła"""
    driver.find_element(By.ID, "username").send_keys("testuser")
    driver.find_element(By.ID, "email").send_keys("test@example.com")
    driver.find_element(By.ID, "password").send_keys("short")
    driver.find_element(By.CSS_SELECTOR, "button.btn-register").click()

    flashes = get_flashes(driver)
    assert any("Password has to be at least 8 characters long" in f.text for f in flashes)


def test_duplicate_email_shows_error(driver):
    """Sprawdza komunikat przy próbie rejestracji istniejącym e-mailem"""
    driver.find_element(By.ID, "username").send_keys("uniqueuser")
    driver.find_element(By.ID, "email").send_keys("rampam@gmail.com")  # istniejący email
    driver.find_element(By.ID, "password").send_keys("validpassword")
    driver.find_element(By.CSS_SELECTOR, "button.btn-register").click()

    flashes = get_flashes(driver)
    assert any("There is account with this email already." in f.text for f in flashes)


def test_duplicate_username_shows_error(driver):
    """Sprawdza komunikat przy próbie rejestracji istniejącym loginem"""
    driver.find_element(By.ID, "username").send_keys("marysia123")  # istniejący username
    driver.find_element(By.ID, "email").send_keys("test@example.pl")
    driver.find_element(By.ID, "password").send_keys("validpassword")
    driver.find_element(By.CSS_SELECTOR, "button.btn-register").click()

    flashes = get_flashes(driver)
    assert any("Username is taken. Pick another one." in f.text for f in flashes)


def test_successful_registration(driver):
    """Sprawdza poprawną rejestrację nowego użytkownika"""
    random_suffix = ''.join(random.choices(string.ascii_letters, k=5))
    unique_username = f"testuser{random_suffix}"
    unique_email = f"test{random_suffix}@example.com"

    driver.find_element(By.ID, "username").send_keys(unique_username)
    driver.find_element(By.ID, "email").send_keys(unique_email)
    driver.find_element(By.ID, "password").send_keys("validpassword")
    driver.find_element(By.CSS_SELECTOR, "button.btn-register").click()

    flashes = get_flashes(driver)
    assert any("Account is created! You can log in now." in f.text for f in flashes)
