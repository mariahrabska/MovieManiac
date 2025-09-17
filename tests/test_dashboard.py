import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

class DashboardPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        chrome_options = Options()
        # chrome_options.add_argument("--headless=new")  # opcjonalnie uruchomienie w trybie headless
        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.wait = WebDriverWait(cls.driver, 10)

        # Otwieramy stronę logowania
        cls.driver.get("http://127.0.0.1:5000/login")

        # Logowanie użytkownika testowego
        username_input = cls.wait.until(EC.presence_of_element_located((By.ID, "email")))
        password_input = cls.driver.find_element(By.ID, "password")

        username_input.send_keys("rampam@gmail.com")
        password_input.send_keys("rampam123")
        password_input.send_keys(Keys.RETURN)

        # Oczekiwanie na załadowanie dashboardu
        cls.wait.until(EC.title_contains("🎬 Find recommendations"))

    @classmethod
    def tearDownClass(cls):
        # Zamknięcie przeglądarki po zakończeniu testów
        cls.driver.quit()

    def test_page_title(self):
        """Sprawdza, czy tytuł strony zawiera poprawny tekst"""
        self.assertIn("🎬 Find recommendations", self.driver.title)

    def test_movie_input_exists(self):
        """Sprawdza, czy istnieje pole do wpisania tytułu filmu"""
        input_box = self.wait.until(EC.presence_of_element_located((By.ID, "movie_title_input")))
        self.assertTrue(input_box.is_displayed())

    def test_submit_button_exists(self):
        """Sprawdza, czy przycisk wyszukiwania rekomendacji istnieje i ma poprawny tekst"""
        button = self.driver.find_element(By.CSS_SELECTOR, "button.btn.btn-primary")
        self.assertTrue(button.is_displayed())
        self.assertEqual(button.text, "Show Recommendations")

    def test_error_shown_for_invalid_movie(self):
        """Sprawdza, czy po wpisaniu nieistniejącego filmu pojawia się komunikat błędu"""
        input_box = self.driver.find_element(By.ID, "movie_title_input")
        button = self.driver.find_element(By.CSS_SELECTOR, "button.btn.btn-primary")

        # Wyczyść pole i wpisz błędną nazwę filmu
        input_box.clear()
        input_box.send_keys("Movie doesn't exist")
        button.click()

        # Sprawdź, czy komunikat błędu jest widoczny
        error_div = self.wait.until(EC.visibility_of_element_located((By.ID, "movie_error")))
        self.assertIn("❌ Please select a movie from the suggestions list", error_div.text)

    def test_input_autocomplete_options(self):
        """Sprawdza, czy po wpisaniu litery pojawiają się propozycje filmów (autocomplete)"""
        input_box = self.driver.find_element(By.ID, "movie_title_input")
        input_box.clear()
        input_box.send_keys("A")

        # Poczekaj, aż lista opcji zostanie uzupełniona
        self.wait.until(lambda driver: len(driver.find_elements(By.CSS_SELECTOR, "#movie_titles option")) > 0)
        options = self.driver.find_elements(By.CSS_SELECTOR, "#movie_titles option")
        self.assertGreater(len(options), 0)


if __name__ == "__main__":
    unittest.main()
