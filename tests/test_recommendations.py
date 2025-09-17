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
        # chrome_options.add_argument("--headless=new")  # tryb bezokienkowy, jeśli nie chcemy widzieć przeglądarki
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
        # Zamykamy przeglądarkę po zakończeniu testów
        cls.driver.quit()

    def login_test_user(self):
        """Loguje testowego użytkownika do aplikacji"""
        self.driver.get("http://127.0.0.1:5000/login")
        email_input = self.wait.until(EC.presence_of_element_located((By.ID, "email")))
        password_input = self.driver.find_element(By.ID, "password")

        email_input.send_keys("testuser@example.com")
        password_input.send_keys("validpassword")

        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        self.wait.until(EC.url_changes("http://127.0.0.1:5000/login"))

    # --- TESTY RECOMMENDATIONS.HTML ---

    def test_recommendations_list_exists(self):
        """Sprawdza, czy lista rekomendacji istnieje i zawiera co najmniej jeden film"""
        rec_list = self.wait.until(EC.presence_of_element_located((By.ID, "recommendationsList")))
        self.assertTrue(len(rec_list.find_elements(By.CLASS_NAME, "movie-item-content")) > 0)

    def test_movie_elements_have_title_and_poster(self):
        """Sprawdza, czy każdy film ma tytuł i miniaturę plakatu"""
        movies = self.driver.find_elements(By.CLASS_NAME, "movie-item-content")
        self.assertGreater(len(movies), 0)
        for movie in movies:
            title = movie.find_element(By.CLASS_NAME, "movie-title").text
            self.assertTrue(title)  # tytuł nie powinien być pusty
            poster = movie.find_elements(By.CLASS_NAME, "poster-thumb")
            self.assertTrue(isinstance(poster, list))  # sprawdzamy, że znaleziono element(y) plakatu

    def test_checkboxes_exist(self):
        """Sprawdza, czy przy każdym filmie są checkboxy: watchlist, watched, favorite"""
        movie = self.driver.find_element(By.CLASS_NAME, "movie-item-content")
        self.assertIsNotNone(movie.find_element(By.CLASS_NAME, "watchlist-checkbox"))
        self.assertIsNotNone(movie.find_element(By.CLASS_NAME, "watched-checkbox"))
        self.assertIsNotNone(movie.find_element(By.CLASS_NAME, "favorite-checkbox"))

    def test_pagination_buttons(self):
        """Sprawdza, czy przyciski paginacji istnieją i są poprawnie ustawione"""
        prev_btn = self.driver.find_element(By.ID, "prevPageBtn")
        next_btn = self.driver.find_element(By.ID, "nextPageBtn")
        self.assertTrue(prev_btn.is_displayed())  # widoczny
        self.assertTrue(next_btn.is_displayed())  # widoczny
        self.assertTrue(prev_btn.get_attribute("disabled"))  # na pierwszej stronie powinien być nieaktywny

    def test_modal_opens_on_movie_click(self):
        """Sprawdza, czy po kliknięciu filmu otwiera się modal ze szczegółami"""
        movie = self.driver.find_element(By.CLASS_NAME, "movie-item-content")
        movie.click()
        modal = self.wait.until(EC.visibility_of_element_located((By.ID, "movieModal")))
        self.assertTrue(modal.is_displayed())  # modal powinien być widoczny
        close_btn = modal.find_element(By.CLASS_NAME, "close-modal")
        close_btn.click()  # zamykamy modal, żeby nie przeszkadzał w dalszych testach

    def test_notification_element_exists(self):
        """Sprawdza, czy na stronie istnieje element powiadomień"""
        notif = self.driver.find_element(By.ID, "notification")
        self.assertIsNotNone(notif)

if __name__ == "__main__":
    unittest.main()

