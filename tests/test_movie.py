import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

class MoviePageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        chrome_options = Options()
        # chrome_options.add_argument("--headless=new")  # tryb bezokienkowy, jeśli chcemy uruchamiać testy w tle
        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.wait = WebDriverWait(cls.driver, 10)

        # --- Logowanie testowego użytkownika ---
        cls.driver.get("http://127.0.0.1:5000/login")
        email_input = cls.wait.until(EC.presence_of_element_located((By.ID, "email")))
        password_input = cls.driver.find_element(By.ID, "password")

        email_input.send_keys("rampam@gmail.com")
        password_input.send_keys("rampam123")
        password_input.send_keys(Keys.RETURN)

        # Czekamy, aż dashboard się załaduje (tytuł strony zawiera "Find recommendations")
        cls.wait.until(EC.title_contains("🎬 Find recommendations"))

        # --- Przejście na stronę konkretnego filmu ---
        cls.driver.get("http://127.0.0.1:5000/movie/1")
        cls.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.movie-details")))

    @classmethod
    def tearDownClass(cls):
        # Zamknięcie przeglądarki po wszystkich testach
        cls.driver.quit()

    def test_page_title_contains_movie_title(self):
        """Sprawdza, czy tytuł strony zawiera ikonę 🎬 (symbol filmu)"""
        title = self.driver.title
        self.assertIn("🎬", title)

    def test_movie_main_elements_exist(self):
        """Sprawdza, czy główne elementy strony filmu istnieją (plakat, tytuł, tagline, ocena, opis)"""
        # Plakat
        poster = self.driver.find_elements(By.CSS_SELECTOR, "img.poster-thumb")
        self.assertIsInstance(poster, list)

        # Tytuł (h1)
        h1 = self.driver.find_element(By.CSS_SELECTOR, "div.movie-main-info h1")
        self.assertTrue(len(h1.text) > 0)

        # Tagline (opcjonalny)
        tagline = self.driver.find_elements(By.CSS_SELECTOR, "div.movie-main-info h3 em")
        if tagline:
            self.assertTrue(len(tagline[0].text) > 0)

        # Ocena (gwiazdki)
        rating = self.driver.find_element(By.CSS_SELECTOR, "div.movie-main-info p")
        self.assertIn("⭐", rating.text)

        # Opis filmu
        overview = self.driver.find_element(By.CSS_SELECTOR, "div.movie-main-info p:nth-of-type(2)")
        self.assertTrue(len(overview.text) > 0)

    def test_additional_info_exists(self):
        """Sprawdza, czy wyświetlane są dodatkowe informacje o filmie (Status, Data premiery)"""
        info_items = self.driver.find_elements(By.CSS_SELECTOR, "div.movie-additional-info ul li")
        self.assertGreater(len(info_items), 0)  # musi być co najmniej 1 element
        texts = [li.text for li in info_items]
        self.assertTrue(any("Status" in t for t in texts))
        self.assertTrue(any("Release Date" in t for t in texts))

if __name__ == "__main__":
    unittest.main()
