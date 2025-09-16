# tests/test_register.py
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException
import random
import string

class RegisterPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        options = Options()
        options.add_argument("--headless")
        service = Service()
        cls.driver = webdriver.Firefox(service=service, options=options)
        cls.driver.delete_all_cookies()
        cls.wait = WebDriverWait(cls.driver, 10)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def setUp(self):
        self.driver.get("http://127.0.0.1:5000/register")
        self.wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

    def _get_flashes(self):
        """Pobiera flash messages z DOM po submit, czeka maks. 5s"""
        try:
            flashes = WebDriverWait(self.driver, 5).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul.flashes li"))
            )
        except TimeoutException:
            flashes = []
        return flashes

    # --- TESTY ---

    def test_page_title(self):
        self.assertIn("⚡ MovieManiac: Register", self.driver.title)

    def test_input_fields_exist(self):
        username = self.wait.until(EC.presence_of_element_located((By.ID, "username")))
        email = self.driver.find_element(By.ID, "email")
        password = self.driver.find_element(By.ID, "password")
        self.assertIsNotNone(username)
        self.assertIsNotNone(email)
        self.assertIsNotNone(password)

    def test_submit_button_exists(self):
        button = self.driver.find_element(By.CSS_SELECTOR, "button.btn-register")
        self.assertIsNotNone(button)

    def test_invalid_email_shows_error(self):
        """Sprawdza JS validation dla niepoprawnego emaila."""
        username_input = self.driver.find_element(By.ID, "username")
        email_input = self.driver.find_element(By.ID, "email")
        password_input = self.driver.find_element(By.ID, "password")
        form = self.driver.find_element(By.CSS_SELECTOR, "form.register-form")

        username_input.clear()
        username_input.send_keys("testuser")
        email_input.clear()
        email_input.send_keys("invalidemail")
        password_input.clear()
        password_input.send_keys("password123")

        # submit przez JS, żeby trigger JS validation
        self.driver.execute_script("arguments[0].submit();", form)

        flashes = self._get_flashes()
        self.assertTrue(any('Email has to contain "@" and "."' in f.text for f in flashes))

    def test_short_password_shows_error(self):
        username_input = self.driver.find_element(By.ID, "username")
        email_input = self.driver.find_element(By.ID, "email")
        password_input = self.driver.find_element(By.ID, "password")
        submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button.btn-register")

        username_input.clear()
        username_input.send_keys("testuser")
        email_input.clear()
        email_input.send_keys("test@example.com")
        password_input.clear()
        password_input.send_keys("short")
        submit_btn.click()

        flashes = self._get_flashes()
        self.assertTrue(any("Password has to be at least 8 characters long" in f.text for f in flashes))

    def test_duplicate_email_shows_error(self):
        username_input = self.driver.find_element(By.ID, "username")
        email_input = self.driver.find_element(By.ID, "email")
        password_input = self.driver.find_element(By.ID, "password")
        submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button.btn-register")

        username_input.clear()
        username_input.send_keys("uniqueuser")
        email_input.clear()
        email_input.send_keys("rampam@gmail.com")  # istniejący email
        password_input.clear()
        password_input.send_keys("validpassword")
        submit_btn.click()

        flashes = self._get_flashes()
        self.assertTrue(any("There is account with this email already." in f.text for f in flashes))

    def test_duplicate_username_shows_error(self):
        username_input = self.driver.find_element(By.ID, "username")
        email_input = self.driver.find_element(By.ID, "email")
        password_input = self.driver.find_element(By.ID, "password")
        submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button.btn-register")

        username_input.clear()
        username_input.send_keys("marysia123")  # istniejący username
        email_input.clear()
        email_input.send_keys("test@example.pl")
        password_input.clear()
        password_input.send_keys("validpassword")
        submit_btn.click()

        flashes = self._get_flashes()
        self.assertTrue(any("Username is taken. Pick another one." in f.text for f in flashes))

    def test_successful_registration(self):
        username_input = self.driver.find_element(By.ID, "username")
        email_input = self.driver.find_element(By.ID, "email")
        password_input = self.driver.find_element(By.ID, "password")
        submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button.btn-register")

        random_suffix = ''.join(random.choices(string.ascii_letters, k=5))
        unique_username = f"testuser{random_suffix}"
        unique_email = f"test{random_suffix}@example.com"

        username_input.clear()
        username_input.send_keys(unique_username)
        email_input.clear()
        email_input.send_keys(unique_email)
        password_input.clear()
        password_input.send_keys("validpassword")
        submit_btn.click()

        flashes = self._get_flashes()
        self.assertTrue(any("Account is created! You can log in now." in f.text for f in flashes))


if __name__ == "__main__":
    unittest.main()
