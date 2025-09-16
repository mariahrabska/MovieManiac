import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

class LoginPageTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        chrome_options = Options()
        # chrome_options.add_argument("--headless=new")  # opcjonalnie tryb headless
        # Selenium Manager automatycznie obsłuży drivera
        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.wait = WebDriverWait(cls.driver, 10)
        cls.driver.get("http://127.0.0.1:5000/login")

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_page_title(self):
        """Sprawdza, czy tytuł strony zawiera 'Login'"""
        self.assertIn("⚡ MovieManiac: Login", self.driver.title)

    def test_email_input_exists(self):
        email_input = self.wait.until(EC.presence_of_element_located((By.ID, "email")))
        self.assertIsNotNone(email_input)

    def test_password_input_exists(self):
        password_input = self.driver.find_element(By.ID, "password")
        self.assertIsNotNone(password_input)

    def test_toggle_password_button_exists(self):
        toggle_btn = self.driver.find_element(By.ID, "togglePassword")
        self.assertIsNotNone(toggle_btn)

    def test_login_button_exists(self):
        login_btn = self.driver.find_element(By.CSS_SELECTOR, "button.btn-login")
        self.assertIsNotNone(login_btn)

    def test_toggle_password_functionality(self):
        password_input = self.driver.find_element(By.ID, "password")
        toggle_btn = self.driver.find_element(By.ID, "togglePassword")

        self.assertEqual(password_input.get_attribute("type"), "password")
        toggle_btn.click()
        self.assertEqual(password_input.get_attribute("type"), "text")
        toggle_btn.click()
        self.assertEqual(password_input.get_attribute("type"), "password")

    def test_register_link_exists(self):
        register_link = self.driver.find_element(By.CSS_SELECTOR, ".register-link a")
        self.assertIsNotNone(register_link)
        self.assertIn("/register", register_link.get_attribute("href"))

    def test_submit_empty_form_shows_error(self):
        login_btn = self.driver.find_element(By.CSS_SELECTOR, "button.btn-login")
        login_btn.click()
        email_input = self.driver.find_element(By.ID, "email")
        self.assertTrue(email_input.get_attribute("validationMessage") != "")

if __name__ == "__main__":
    unittest.main()
