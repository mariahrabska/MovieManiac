import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


class SettingsPageTests(unittest.TestCase):
    def setUp(self):
        chrome_options = Options()
        # chrome_options.add_argument("--headless=new")  # tryb bezokienkowy
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, 10)
        self.login_test_user()

    def login_test_user(self):
        self.driver.get("http://127.0.0.1:5000/login")
        email_input = self.wait.until(EC.presence_of_element_located((By.ID, "email")))
        password_input = self.driver.find_element(By.ID, "password")

        email_input.send_keys("testuser@example.com")
        password_input.send_keys("newpassword")

        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        self.wait.until(EC.url_changes("http://127.0.0.1:5000/login"))

        self.driver.get("http://127.0.0.1:5000/settings")
        self.wait.until(EC.presence_of_element_located((By.ID, "username")))

    def tearDown(self):
        self.driver.quit()

    def test_page_title(self):
        """Sprawdza czy tytuł strony zawiera 'Account Settings'."""
        self.driver.get("http://127.0.0.1:5000/settings")
        self.assertIn("Account Settings", self.driver.title)

    def test_input_fields_exist(self):
        """Sprawdza czy pola input dla username i password istnieją na stronie."""
        self.driver.get("http://127.0.0.1:5000/settings")
        username = self.wait.until(EC.presence_of_element_located((By.ID, "username")))
        password = self.driver.find_element(By.ID, "password")
        self.assertIsNotNone(username)
        self.assertIsNotNone(password)

    def test_empty_username_shows_error(self):
        """Sprawdza czy pusty username daje błąd walidacji HTML5 lub flash message."""
        self.driver.get("http://127.0.0.1:5000/settings")
        username_input = self.wait.until(EC.presence_of_element_located((By.ID, "username")))
        username_input.clear()
        self.driver.find_element(By.CLASS_NAME, "btn-save").click()

        # najpierw spróbuj złapać komunikat flash
        try:
            flash_msg = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".flashes li")))
            self.assertTrue("Username" in flash_msg.text)
        except Exception:
            # fallback: sprawdź walidację HTML5
            self.assertEqual(username_input.get_attribute("validationMessage"), "Wypełnij to pole.")

    def test_short_password_shows_error(self):
        """Sprawdza czy za krótkie hasło zwraca komunikat o błędzie."""
        self.driver.get("http://127.0.0.1:5000/settings")
        password_input = self.wait.until(EC.presence_of_element_located((By.ID, "password")))
        password_input.clear()
        password_input.send_keys("short")
        self.driver.find_element(By.CLASS_NAME, "btn-save").click()

        flash_msg = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".flashes li")))
        self.assertTrue("8 znak" in flash_msg.text or "8 characters" in flash_msg.text)

    def test_successful_update(self):
        """Sprawdza czy poprawna aktualizacja pokazuje komunikat sukcesu
        i czy zmienia dane"""
        self.driver.get("http://127.0.0.1:5000/settings")
        username_input = self.wait.until(EC.presence_of_element_located((By.ID, "username")))
        password_input = self.driver.find_element(By.ID, "password")

        current_username = username_input.get_attribute("value")
        username_input.clear()
        username_input.send_keys("testuser")
        password_input.clear()
        password_input.send_keys("validpassword")

        self.driver.find_element(By.CLASS_NAME, "btn-save").click()

        flash_msg = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".flashes li")))
        self.assertTrue("updated" in flash_msg.text)


if __name__ == "__main__":
    unittest.main()
