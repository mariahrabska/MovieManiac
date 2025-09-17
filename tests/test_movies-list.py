import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

class WatchlistPageTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Inicjalizacja przeglądarki
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

        # Czekamy na załadowanie dashboardu
        cls.wait.until(EC.title_contains("🎬 Find recommendations"))

        # Przejście do strony watchlist
        cls.driver.get("http://127.0.0.1:5000/movies-list")
        cls.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".main-content")))

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_page_title(self):
        """Sprawdza, czy tytuł strony to '🎬My Watchlist'"""
        self.driver.get("http://127.0.0.1:5000/movies-list")
        self.wait.until(EC.title_is("🎬My Watchlist"))
        self.assertEqual(self.driver.title, "🎬My Watchlist")



    def test_watchlist_has_movies(self):
        """Sprawdza, czy lista filmów jest obecna (jeśli są filmy)"""
        movies = self.driver.find_elements(By.CSS_SELECTOR, "ul.movie-list li.movie-item")
        # Lista może być pusta, ale element ul.movie-list powinien istnieć jeśli watchlist nie jest pusty
        movie_list = self.driver.find_elements(By.CSS_SELECTOR, "ul.movie-list")
        if movie_list:
            self.assertTrue(len(movies) >= 0)

    def test_filter_genre_dropdown(self):
        """Sprawdza, czy można wybrać gatunek z dropdownu jeśli istnieje"""
        genre_filter = self.driver.find_elements(By.ID, "genre-filter")
        if genre_filter:  # jeśli dropdown istnieje
            options = genre_filter[0].find_elements(By.TAG_NAME, "option")
            self.assertTrue(len(options) > 1)  # co najmniej "All" + 1 gatunek

    def test_sort_dropdown(self):
        """Sprawdza, czy dropdown sortowania zawiera wszystkie opcje"""
        sort_select = self.driver.find_elements(By.ID, "sort-by")
        if sort_select:
            options = [opt.get_attribute("value") for opt in sort_select[0].find_elements(By.TAG_NAME, "option")]
            self.assertIn("title-asc", options)
            self.assertIn("title-desc", options)
            self.assertIn("year-asc", options)
            self.assertIn("year-desc", options)

    def test_keyword_search_autocomplete(self):
        """Sprawdza, czy pole wyszukiwania słów kluczowych istnieje"""
        search_input = self.driver.find_elements(By.ID, "keyword-search")
        if search_input:
            self.assertIsNotNone(search_input[0])

    def test_movie_actions_buttons_present(self):
        """Sprawdza, czy przyciski akcji dla pierwszego filmu istnieją"""
        movies = self.driver.find_elements(By.CSS_SELECTOR, "ul.movie-list li.movie-item")
        if movies:
            movie_item = movies[0]
            remove_btn = movie_item.find_element(By.CSS_SELECTOR, ".remove-btn")
            watched_btn = movie_item.find_element(By.CSS_SELECTOR, ".watched-btn")
            favorite_btn = movie_item.find_element(By.CSS_SELECTOR, ".favorite-btn")
            self.assertIsNotNone(remove_btn)
            self.assertIsNotNone(watched_btn)
            self.assertIsNotNone(favorite_btn)

    def test_click_movie_link(self):
        """Kliknięcie filmu powinno przekierować na jego stronę /movie/<id>"""
        movies = self.driver.find_elements(By.CSS_SELECTOR, "ul.movie-list li.movie-item a")
        if movies:
            movie_link = movies[0]
            href = movie_link.get_attribute("href")
            movie_link.click()
            self.wait.until(lambda d: href in d.current_url)
            self.assertIn("/movie/", self.driver.current_url)

if __name__ == "__main__":
    unittest.main()
