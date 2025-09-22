# tests/test_settings.py
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

# ----------------------
# fixtura globalna dla większości testów
# ----------------------
@pytest.fixture(scope="module")
def driver():
    chrome_options = Options()
    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()
    wait = WebDriverWait(driver, 10)

    # Logowanie użytkownika
    driver.get("http://127.0.0.1:5000/login")
    email_input = wait.until(EC.presence_of_element_located((By.ID, "email")))
    password_input = driver.find_element(By.ID, "password")
    email_input.send_keys("testuser@example.com")
    password_input.send_keys("validpassword")
    password_input.send_keys(Keys.RETURN)
    wait.until(EC.url_changes("http://127.0.0.1:5000/login"))

    # Przejście do ustawień
    driver.get("http://127.0.0.1:5000/settings")
    wait.until(EC.presence_of_element_located((By.ID, "username")))

    yield driver
    driver.quit()


# ----------------------
# fixtura lokalna tylko dla testu short password
# ----------------------
@pytest.fixture
def driver_short_password():
    chrome_options = Options()
    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()
    wait = WebDriverWait(driver, 10)

    # Logowanie użytkownika
    driver.get("http://127.0.0.1:5000/login")
    email_input = wait.until(EC.presence_of_element_located((By.ID, "email")))
    password_input = driver.find_element(By.ID, "password")
    email_input.send_keys("testuser@example.com")
    password_input.send_keys("validpassword")
    password_input.send_keys(Keys.RETURN)
    wait.until(EC.url_changes("http://127.0.0.1:5000/login"))

    # Przejście do ustawień
    driver.get("http://127.0.0.1:5000/settings")
    wait.until(EC.presence_of_element_located((By.ID, "username")))

    yield driver
    driver.quit()


# ----------------------
# TESTY
# ----------------------
def test_page_load_time(driver):
    start_time = time.time()
    driver.get("http://127.0.0.1:5000/settings")
    WebDriverWait(driver, 10).until(lambda d: d.execute_script("return document.readyState") == "complete")
    load_time = time.time() - start_time
    print(f"Czas ładowania strony: {load_time:.2f} sekundy")
    assert load_time <= 3


@pytest.mark.parametrize("width,height", [
    (1920, 1080), (1366, 768), (768, 1024), (414, 896), (375, 812)
])
def test_responsive_layout_settings(driver, width, height):
    driver.set_window_size(width, height)
    wait = WebDriverWait(driver, 10)
    username_input = wait.until(EC.presence_of_element_located((By.ID, "username")))
    password_input = driver.find_element(By.ID, "password")
    save_btn = driver.find_element(By.CLASS_NAME, "btn-save")
    assert username_input.is_displayed()
    assert password_input.is_displayed()
    assert save_btn.is_displayed()
    if width < 600:
        assert save_btn.location['y'] > password_input.location['y']


def test_page_title(driver):
    driver.get("http://127.0.0.1:5000/settings")
    assert "Account Settings" in driver.title


def test_input_fields_exist(driver):
    wait = WebDriverWait(driver, 10)
    username = wait.until(EC.presence_of_element_located((By.ID, "username")))
    password = driver.find_element(By.ID, "password")
    assert username is not None
    assert password is not None


def test_empty_username_shows_error(driver):
    wait = WebDriverWait(driver, 10)
    username_input = wait.until(EC.presence_of_element_located((By.ID, "username")))
    username_input.clear()
    driver.find_element(By.CLASS_NAME, "btn-save").click()
    try:
        flash_msg = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".flashes li")))
        assert "Username" in flash_msg.text
    except Exception:
        assert username_input.get_attribute("validationMessage") == "Wypełnij to pole."


# <-- używamy fixtury driver_short_password tylko dla tego testu -->
def test_short_password_shows_error(driver_short_password):
    wait = WebDriverWait(driver_short_password, 10)
    password_input = wait.until(EC.presence_of_element_located((By.ID, "password")))
    password_input.clear()
    password_input.send_keys("short")
    driver_short_password.find_element(By.CLASS_NAME, "btn-save").click()
    flash_msg = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".flashes li")))
    assert "8 znak" in flash_msg.text or "8 characters" in flash_msg.text


def test_successful_update(driver):
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
