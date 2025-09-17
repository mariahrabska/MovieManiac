import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

class RankingPageTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        chrome_options = Options()
        # chrome_options.add_argument("--headless=new")  # opcjonalnie tryb bezokienkowy
        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.wait = WebDriverWait(cls.driver, 10)

        # Logowanie użytkownika
        cls.driver.get("http://127.0.0.1:5000/login")
        username_input = cls.wait.until(EC.presence_of_element_located((By.ID, "email")))
        password_input = cls.driver.find_element(By.ID, "password")
        username_input.send_keys("rampam@gmail.com")
        password_input.send_keys("rampam123")
        password_input.send_keys(Keys.RETURN)

        # Poczekaj na załadowanie dashboardu
        cls.wait.until(EC.title_contains("🎬 Find recommendations"))

        # Przejście do strony ranking
        cls.driver.get("http://127.0.0.1:5000/ranking")
        cls.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".main-content")))

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_page_title(self):
        """Sprawdza tytuł strony"""
        self.assertEqual(self.driver.title, "🎬Movie Ranking")

    def test_ranking_list_present(self):
        """Sprawdza, czy lista rankingowa istnieje"""
        ranking_list = self.driver.find_elements(By.CSS_SELECTOR, "ul.ranking-list")
        self.assertTrue(len(ranking_list) > 0)

    def test_ranking_items_present(self):
        """Sprawdza, czy lista rankingowa zawiera elementy"""
        items = self.driver.find_elements(By.CSS_SELECTOR, "ul.ranking-list li.ranking-item")
        self.assertTrue(len(items) > 0)

    def test_movie_links(self):
        """Kliknięcie filmu przekierowuje na jego stronę"""
        movie_links = self.driver.find_elements(By.CSS_SELECTOR, "ul.ranking-list li.ranking-item a")
        if movie_links:
            href = movie_links[0].get_attribute("href")
            movie_links[0].click()
            self.wait.until(lambda d: href in d.current_url)
            self.assertIn("/movie/", self.driver.current_url)
            # Wróć do strony ranking, żeby inne testy działały
            self.driver.back()
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".main-content")))

    def test_movie_info_present(self):
        """Sprawdza obecność informacji o filmie: tytuł, ocena, gatunki, opis"""
        items = self.driver.find_elements(By.CSS_SELECTOR, "ul.ranking-list li.ranking-item")
        if items:
            info = items[0].find_element(By.CSS_SELECTOR, ".movie-info")
            title = info.find_element(By.CSS_SELECTOR, ".movie-title")
            vote = info.find_element(By.CSS_SELECTOR, ".vote-average")
            genres = info.find_element(By.CSS_SELECTOR, ".movie-genres")
            desc = info.find_element(By.CSS_SELECTOR, ".movie-description")
            self.assertIsNotNone(title)
            self.assertIsNotNone(vote)
            self.assertIsNotNone(genres)
            self.assertIsNotNone(desc)

    def test_pagination_next(self):
        """Sprawdza obecność przycisku Next"""
        next_btn = self.driver.find_elements(By.CSS_SELECTOR, ".pagination a[href*='page=']")
        self.assertTrue(any("Next" in btn.text for btn in next_btn))

    def test_pagination_previous(self):
        """Sprawdza obecność przycisku Previous, jeśli strona > 1"""
        prev_btn = self.driver.find_elements(By.CSS_SELECTOR, ".pagination a")
        if len(prev_btn) > 1:  # jeśli istnieje Previous
            self.assertTrue(any("Previous" in btn.text for btn in prev_btn))

if __name__ == "__main__":
    unittest.main()
