import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

class RecommendationsPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        chrome_options = Options()
        # chrome_options.add_argument("--headless=new")  # tryb bezokienkowy
        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.driver.maximize_window()
        cls.wait = WebDriverWait(cls.driver, 10)
        cls.login_test_user(cls)

        # Po zalogowaniu przechodzimy na dashboard i wpisujemy tytuł filmu
        cls.driver.get("http://127.0.0.1:5000/dashboard")
        movie_input = cls.wait.until(EC.presence_of_element_located((By.ID, "movie_title_input")))
        movie_input.send_keys("Interstellar (2014)")
        cls.driver.find_element(By.CSS_SELECTOR, "button.btn.btn-primary").click()

        # Czekamy aż załaduje się strona rekomendacji
        cls.wait.until(EC.presence_of_element_located((By.ID, "recommendationsList")))

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def login_test_user(self):
        self.driver.get("http://127.0.0.1:5000/login")
        email_input = self.wait.until(EC.presence_of_element_located((By.ID, "email")))
        password_input = self.driver.find_element(By.ID, "password")

        email_input.send_keys("testuser@example.com")
        password_input.send_keys("newpassword")

        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        self.wait.until(EC.url_changes("http://127.0.0.1:5000/login"))

    # --- TESTY RECOMMENDATIONS.HTML ---

    def test_recommendations_list_exists(self):
        rec_list = self.wait.until(EC.presence_of_element_located((By.ID, "recommendationsList")))
        self.assertTrue(len(rec_list.find_elements(By.CLASS_NAME, "movie-item-content")) > 0)

    def test_movie_elements_have_title_and_poster(self):
        movies = self.driver.find_elements(By.CLASS_NAME, "movie-item-content")
        self.assertGreater(len(movies), 0)
        for movie in movies:
            title = movie.find_element(By.CLASS_NAME, "movie-title").text
            self.assertTrue(title)
            poster = movie.find_elements(By.CLASS_NAME, "poster-thumb")
            self.assertTrue(isinstance(poster, list))

    def test_checkboxes_exist(self):
        movie = self.driver.find_element(By.CLASS_NAME, "movie-item-content")
        self.assertIsNotNone(movie.find_element(By.CLASS_NAME, "watchlist-checkbox"))
        self.assertIsNotNone(movie.find_element(By.CLASS_NAME, "watched-checkbox"))
        self.assertIsNotNone(movie.find_element(By.CLASS_NAME, "favorite-checkbox"))

    def test_pagination_buttons(self):
        prev_btn = self.driver.find_element(By.ID, "prevPageBtn")
        next_btn = self.driver.find_element(By.ID, "nextPageBtn")
        self.assertTrue(prev_btn.is_displayed())
        self.assertTrue(next_btn.is_displayed())
        self.assertTrue(prev_btn.get_attribute("disabled"))

    def test_modal_opens_on_movie_click(self):
        movie = self.driver.find_element(By.CLASS_NAME, "movie-item-content")
        movie.click()
        modal = self.wait.until(EC.visibility_of_element_located((By.ID, "movieModal")))
        self.assertTrue(modal.is_displayed())
        close_btn = modal.find_element(By.CLASS_NAME, "close-modal")
        close_btn.click()

    def test_notification_element_exists(self):
        notif = self.driver.find_element(By.ID, "notification")
        self.assertIsNotNone(notif)

if __name__ == "__main__":
    unittest.main()
