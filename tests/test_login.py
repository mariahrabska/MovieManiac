import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


@pytest.fixture(scope="module")
def driver():
    """Fixture: uruchamia i zamyka przeglądarkę dla wszystkich testów"""
    chrome_options = Options()
    # chrome_options.add_argument("--headless=new")  # uruchom w trybie headless jeśli chcesz bez okna

    # Uruchamiamy Chrome przez Selenium
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)

    # Przechodzimy na stronę logowania
    driver.get("http://127.0.0.1:5000/login")

    # Zwracamy driver + wait do testów
    yield driver, wait

    # Po zakończeniu testów zamykamy przeglądarkę
    driver.quit()


def test_page_title(driver):
    """Sprawdza, czy tytuł strony logowania zawiera właściwy tekst"""
    drv, _ = driver
    assert "⚡ MovieManiac: Login" in drv.title


def test_email_input_exists(driver):
    """Sprawdza, czy pole e-mail jest obecne na stronie"""
    drv, wait = driver
    email_input = wait.until(EC.presence_of_element_located((By.ID, "email")))
    assert email_input is not None


def test_password_input_exists(driver):
    """Sprawdza, czy pole hasła jest obecne na stronie"""
    drv, _ = driver
    password_input = drv.find_element(By.ID, "password")
    assert password_input is not None


def test_toggle_password_button_exists(driver):
    """Sprawdza, czy istnieje przycisk do pokazywania/ukrywania hasła"""
    drv, _ = driver
    toggle_btn = drv.find_element(By.ID, "togglePassword")
    assert toggle_btn is not None


def test_login_button_exists(driver):
    """Sprawdza, czy przycisk logowania jest obecny"""
    drv, _ = driver
    login_btn = drv.find_element(By.CSS_SELECTOR, "button.btn-primary")
    assert login_btn is not None


def test_toggle_password_functionality(driver):
    """Sprawdza działanie przełącznika widoczności hasła"""
    drv, _ = driver
    password_input = drv.find_element(By.ID, "password")
    toggle_btn = drv.find_element(By.ID, "togglePassword")

    # Początkowo pole powinno mieć typ 'password'
    assert password_input.get_attribute("type") == "password"

    # Kliknięcie zmienia typ na 'text'
    toggle_btn.click()
    assert password_input.get_attribute("type") == "text"

    # Kolejne kliknięcie wraca do 'password'
    toggle_btn.click()
    assert password_input.get_attribute("type") == "password"


def test_register_link_exists(driver):
    """Sprawdza, czy link do rejestracji istnieje i prowadzi do /register"""
    drv, _ = driver
    register_link = drv.find_element(By.CSS_SELECTOR, ".register-link a")
    assert register_link is not None
    assert "/register" in register_link.get_attribute("href")


def test_submit_empty_form_shows_error(driver):
    """Sprawdza, czy wysłanie pustego formularza wywołuje walidację"""
    drv, _ = driver
    login_btn = drv.find_element(By.CSS_SELECTOR, "button.btn-primary")

    # Klikamy logowanie bez wypełniania formularza
    login_btn.click()

    # Pole e-mail powinno zgłosić błąd walidacji HTML5
    email_input = drv.find_element(By.ID, "email")
    assert email_input.get_attribute("validationMessage") != ""
