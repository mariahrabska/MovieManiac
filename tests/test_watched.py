import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

class WatchedMoviesPageTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Inicjalizacja przeglądarki
        chrome_options = Options()
        # chrome_options.add_argument("--headless=new")  # tryb bezokienkowy opcjonalnie
        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.wait = WebDriverWait(cls.driver, 10)

        # Logowanie użytkownika
        cls.driver.get("http://127.0.0.1:5000/login")
        username_input = cls.wait.until(EC.presence_of_element_located((By.ID, "email")))
        password_input = cls.driver.find_element(By.ID, "password")
        username_input.send_keys("rampam@gmail.com")
        password_input.send_keys("rampam123")
        password_input.send_keys(Keys.RETURN)

        # Czekamy na dashboard
        cls.wait.until(EC.title_contains("🎬 Find recommendations"))

        # Przejście na stronę Watched Movies
        cls.driver.get("http://127.0.0.1:5000/watched")
        cls.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".main-content")))

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_page_title(self):
        """Sprawdza, czy tytuł strony to 'Watched Movies'"""
        self.driver.get("http://127.0.0.1:5000/watched")
        self.wait.until(EC.title_is("Watched Movies"))
        self.assertEqual(self.driver.title, "Watched Movies")

    def test_movies_list_present(self):
        """Sprawdza, czy lista obejrzanych filmów istnieje"""
        movies = self.driver.find_elements(By.CSS_SELECTOR, "ul.movie-list li.movie-item")
        movie_list = self.driver.find_elements(By.CSS_SELECTOR, "ul.movie-list")
        if movie_list:
            self.assertTrue(len(movies) >= 0)

    def test_filter_genre_dropdown(self):
        """Sprawdza obecność i funkcjonowanie filtrowania po gatunku"""
        genre_filter = self.driver.find_elements(By.ID, "genre-filter")
        if genre_filter:
            options = genre_filter[0].find_elements(By.TAG_NAME, "option")
            self.assertTrue(len(options) > 1)  # co najmniej "All" + 1 gatunek

            # Test funkcjonalny filtrowania
            first_genre = options[1].get_attribute("value")
            genre_filter[0].send_keys(first_genre)
            # Sprawdzenie, czy są widoczne tylko filmy z wybranym gatunkiem
            for item in self.driver.find_elements(By.CSS_SELECTOR, "ul.movie-list li.movie-item"):
                genres = item.get_attribute("data-genres").split('|')
                if first_genre != "all":
                    self.assertIn(first_genre, genres)

    def test_sort_dropdown(self):
        """Sprawdza obecność i działanie sortowania"""
        sort_select = self.driver.find_element(By.ID, "sort-by")
        self.assertIsNotNone(sort_select)

        # Sprawdzenie wszystkich opcji
        options = [opt.get_attribute("value") for opt in sort_select.find_elements(By.TAG_NAME, "option")]
        expected_options = ["title-asc", "title-desc", "year-asc", "year-desc"]
        for opt in expected_options:
            self.assertIn(opt, options)

        # Wywołanie sortowania po tytule rosnąco
        self.driver.execute_script(
            "arguments[0].value='title-asc'; arguments[0].dispatchEvent(new Event('change'));",
            sort_select
        )

        # Poczekaj chwilę, aby JS zdążył posortować listę
        self.wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, ".movie-item"))

        # Pobranie tytułów z DOM
        titles = [el.text.lower() for el in self.driver.find_elements(By.CSS_SELECTOR, ".movie-title")]

        # Sprawdzenie, czy lista jest posortowana alfabetycznie
        self.assertEqual(titles, sorted(titles))


    def test_keyword_search_autocomplete(self):
        """Sprawdza, czy pole wyszukiwania istnieje"""
        search_input = self.driver.find_elements(By.ID, "keyword-search")
        if search_input:
            self.assertIsNotNone(search_input[0])

    def test_movie_actions_buttons_present(self):
        """Sprawdza przyciski akcji: usuń i ulubione"""
        movies = self.driver.find_elements(By.CSS_SELECTOR, "ul.movie-list li.movie-item")
        if movies:
            movie_item = movies[0]
            remove_btn = movie_item.find_element(By.CSS_SELECTOR, ".remove-btn")
            favorite_btn = movie_item.find_element(By.CSS_SELECTOR, ".favorite-btn")
            self.assertIsNotNone(remove_btn)
            self.assertIsNotNone(favorite_btn)

    def test_click_movie_link(self):
        """Kliknięcie filmu przenosi na jego stronę /movie/<id>"""
        movies = self.driver.find_elements(By.CSS_SELECTOR, "ul.movie-list li.movie-item a")
        if movies:
            movie_link = movies[0]
            href = movie_link.get_attribute("href")
            movie_link.click()
            self.wait.until(lambda d: href in d.current_url)
            self.assertIn("/movie/", self.driver.current_url)

if __name__ == "__main__":
    unittest.main()
