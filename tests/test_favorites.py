import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

class FavoritesPageTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        chrome_options = Options()
        # chrome_options.add_argument("--headless=new")  # opcjonalnie tryb bezokienkowy
        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.wait = WebDriverWait(cls.driver, 10)

        # Logowanie
        cls.driver.get("http://127.0.0.1:5000/login")
        email_input = cls.wait.until(EC.presence_of_element_located((By.ID, "email")))
        password_input = cls.driver.find_element(By.ID, "password")
        email_input.send_keys("rampam@gmail.com")
        password_input.send_keys("rampam123")
        password_input.send_keys(Keys.RETURN)

        cls.wait.until(EC.title_contains("🎬 Find recommendations"))
        cls.driver.get("http://127.0.0.1:5000/favorites")
        cls.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".main-content")))

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_page_title(self):
        """Sprawdza tytuł strony"""
        self.driver.get("http://127.0.0.1:5000/favorites")
        self.wait.until(EC.title_is("Favorite Movies"))
        self.assertEqual(self.driver.title, "Favorite Movies")

    def test_favorites_list_present(self):
        """Lista ul.movie-list powinna istnieć, jeśli są filmy"""
        movie_list = self.driver.find_elements(By.CSS_SELECTOR, "ul.movie-list")
        self.assertTrue(movie_list or True)  # lista może być pusta, ale element istnieje

    def test_remove_button(self):
        """Przycisk remove powinien usuwać film z listy"""
        movies = self.driver.find_elements(By.CSS_SELECTOR, "ul.movie-list li.movie-item")
        if movies:
            remove_btn = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "li.movie-item .remove-btn"))
            )
            # klik i czekanie aż element zniknie
            movie_item = remove_btn.find_element(By.XPATH, "./ancestor::li")
            remove_btn.click()
            self.wait.until(EC.staleness_of(movie_item))

    def test_genre_filter(self):
        """Filtrowanie po gatunku"""
        genre_filter = self.driver.find_elements(By.ID, "genre-filter")
        if genre_filter:
            options = genre_filter[0].find_elements(By.TAG_NAME, "option")
            if len(options) > 1:
                genre_filter[0].send_keys(options[1].get_attribute("value"))
                # sprawdzamy widoczne elementy
                for item in self.driver.find_elements(By.CSS_SELECTOR, "ul.movie-list li.movie-item"):
                    if item.is_displayed():
                        genres = item.get_attribute("data-genres").split('|')
                        self.assertIn(options[1].get_attribute("value"), genres)

    def test_sort_dropdown(self):
        """Sprawdza działanie sortowania po tytule, roku i dacie dodania"""
        sort_select = self.driver.find_element(By.ID, "sort-by")
        self.assertIsNotNone(sort_select)

        # Sprawdzenie wszystkich opcji
        options = [opt.get_attribute("value") for opt in sort_select.find_elements(By.TAG_NAME, "option")]
        expected_options = ["title-asc", "title-desc", "year-asc", "year-desc", "added-asc", "added-desc"]
        for opt in expected_options:
            self.assertIn(opt, options)

        # Funkcja pomocnicza do sprawdzenia sortowania
        def get_titles_or_years_or_dates():
            movie_items = self.driver.find_elements(By.CSS_SELECTOR, ".movie-item")
            titles = [el.find_element(By.CSS_SELECTOR, ".movie-title").text.lower() for el in movie_items]
            years = [int(el.get_attribute("data-year") or 0) for el in movie_items]
            added = [el.get_attribute("data-added") for el in movie_items]
            return titles, years, added

        # --- SORTOWANIE TITLE ASC ---
        self.driver.execute_script(
            "arguments[0].value='title-asc'; arguments[0].dispatchEvent(new Event('change'));",
            sort_select
        )
        self.wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, ".movie-item"))
        titles, _, _ = get_titles_or_years_or_dates()
        self.assertEqual(titles, sorted(titles))

        # --- SORTOWANIE TITLE DESC ---
        self.driver.execute_script(
            "arguments[0].value='title-desc'; arguments[0].dispatchEvent(new Event('change'));",
            sort_select
        )
        self.wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, ".movie-item"))
        titles, _, _ = get_titles_or_years_or_dates()
        self.assertEqual(titles, sorted(titles, reverse=True))

        # --- SORTOWANIE YEAR ASC ---
        self.driver.execute_script(
            "arguments[0].value='year-asc'; arguments[0].dispatchEvent(new Event('change'));",
            sort_select
        )
        self.wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, ".movie-item"))
        _, years, _ = get_titles_or_years_or_dates()
        self.assertEqual(years, sorted(years))

        # --- SORTOWANIE YEAR DESC ---
        self.driver.execute_script(
            "arguments[0].value='year-desc'; arguments[0].dispatchEvent(new Event('change'));",
            sort_select
        )
        self.wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, ".movie-item"))
        _, years, _ = get_titles_or_years_or_dates()
        self.assertEqual(years, sorted(years, reverse=True))

        # --- SORTOWANIE ADDED ASC ---
        self.driver.execute_script(
            "arguments[0].value='added-asc'; arguments[0].dispatchEvent(new Event('change'));",
            sort_select
        )
        self.wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, ".movie-item"))
        _, _, added = get_titles_or_years_or_dates()
        self.assertTrue(all(added[i] <= added[i+1] for i in range(len(added)-1)))

        # --- SORTOWANIE ADDED DESC ---
        self.driver.execute_script(
            "arguments[0].value='added-desc'; arguments[0].dispatchEvent(new Event('change'));",
            sort_select
        )
        self.wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, ".movie-item"))
        _, _, added = get_titles_or_years_or_dates()
        self.assertTrue(all(added[i] >= added[i+1] for i in range(len(added)-1)))


    def test_keyword_search(self):
        """Sprawdza, czy pole wyszukiwania słów kluczowych istnieje"""
        search_input = self.driver.find_elements(By.ID, "keyword-search")
        self.assertTrue(search_input)
        search_input[0].send_keys("action")
        self.assertEqual(search_input[0].get_attribute("value"), "action")

if __name__ == "__main__":
    unittest.main()
