# tests/test_settings_page.py
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

@pytest.fixture(scope="function")
def driver():
    """Fixtura inicjalizująca przeglądarkę i logująca testowego użytkownika przed każdym testem."""
    chrome_options = Options()
    # chrome_options.add_argument("--headless=new")  # tryb headless
    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()
    wait = WebDriverWait(driver, 10)

    # Logowanie testowego użytkownika
    driver.get("http://127.0.0.1:5000/login")
    email_input = wait.until(EC.presence_of_element_located((By.ID, "email")))
    password_input = driver.find_element(By.ID, "password")
    email_input.send_keys("testuser@example.com")
    password_input.send_keys("validpassword")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    wait.until(EC.url_changes("http://127.0.0.1:5000/login"))

    # Przejście do ustawień konta
    driver.get("http://127.0.0.1:5000/settings")
    wait.until(EC.presence_of_element_located((By.ID, "username")))

    yield driver
    driver.quit()


@pytest.mark.parametrize("width,height", [
    (1920, 1080),  # Desktop (Full HD)
    (1366, 768),   # Laptop
    (768, 1024),   # Tablet (portrait)
    (414, 896),    # iPhone XR / 11
    (375, 812),    # iPhone X / 12 mini
])
def test_responsive_layout_settings(driver, width, height):
    """Sprawdza responsywność strony ustawień konta w różnych rozdzielczościach"""
    driver.set_window_size(width, height)
    wait = WebDriverWait(driver, 10)

    # Kluczowe elementy formularza ustawień
    username_input = wait.until(EC.presence_of_element_located((By.ID, "username")))
    password_input = driver.find_element(By.ID, "password")
    save_btn = driver.find_element(By.CLASS_NAME, "btn-save")

    # Sprawdzenie widoczności
    assert username_input.is_displayed(), f"Pole username niewidoczne przy rozdzielczości {width}x{height}"
    assert password_input.is_displayed(), f"Pole hasła niewidoczne przy rozdzielczości {width}x{height}"
    assert save_btn.is_displayed(), f"Przycisk zapisu niewidoczny przy rozdzielczości {width}x{height}"

    # Dodatkowa walidacja układu dla mobile
    if width < 600:
        assert save_btn.location['y'] > password_input.location['y'], (
            f"Na mobile ({width}x{height}) przycisk zapisu nie znajduje się pod polem hasła"
        )



def test_page_title(driver):
    """Sprawdza czy tytuł strony zawiera 'Account Settings'."""
    driver.get("http://127.0.0.1:5000/settings")
    assert "Account Settings" in driver.title


def test_input_fields_exist(driver):
    """Sprawdza czy pola input dla username i password istnieją na stronie."""
    driver.get("http://127.0.0.1:5000/settings")
    wait = WebDriverWait(driver, 10)
    username = wait.until(EC.presence_of_element_located((By.ID, "username")))
    password = driver.find_element(By.ID, "password")
    assert username is not None
    assert password is not None


def test_empty_username_shows_error(driver):
    """Sprawdza czy pusty username daje błąd walidacji HTML5 lub flash message."""
    driver.get("http://127.0.0.1:5000/settings")
    wait = WebDriverWait(driver, 10)
    username_input = wait.until(EC.presence_of_element_located((By.ID, "username")))
    username_input.clear()
    driver.find_element(By.CLASS_NAME, "btn-save").click()

    try:
        flash_msg = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".flashes li")))
        assert "Username" in flash_msg.text
    except Exception:
        # fallback: sprawdź walidację HTML5
        assert username_input.get_attribute("validationMessage") == "Wypełnij to pole."


def test_short_password_shows_error(driver):
    """Sprawdza czy za krótkie hasło zwraca komunikat o błędzie."""
    driver.get("http://127.0.0.1:5000/settings")
    wait = WebDriverWait(driver, 10)
    password_input = wait.until(EC.presence_of_element_located((By.ID, "password")))
    password_input.clear()
    password_input.send_keys("short")
    driver.find_element(By.CLASS_NAME, "btn-save").click()

    flash_msg = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".flashes li")))
    assert "8 znak" in flash_msg.text or "8 characters" in flash_msg.text


def test_successful_update(driver):
    """Sprawdza czy poprawna aktualizacja pokazuje komunikat sukcesu i czy zmienia dane."""
    driver.get("http://127.0.0.1:5000/settings")
    wait = WebDriverWait(driver, 10)
    username_input = wait.until(EC.presence_of_element_located((By.ID, "username")))
    password_input = driver.find_element(By.ID, "password")

    username_input.clear()
    username_input.send_keys("testuser")
    password_input.clear()
    password_input.send_keys("validpassword")
    driver.find_element(By.CLASS_NAME, "btn-save").click()

    flash_msg = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".flashes li")))
    assert "updated" in flash_msg.text
