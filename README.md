# MovieManiac

MovieManiac to prosta aplikacja webowa w Pythonie wykorzystująca Flask, która rekomenduje filmy użytkownikom na podstawie ich ocen. Projekt pokazuje podstawy machine learning (algorytm KNN), dynamiczny interfejs z Flask i przechowywanie danych w SQLite.  

---

## Funkcjonalności
- Przeglądanie listy filmów  
- Dodawanie filmów do list: Do obejrzenia, Obejrzane, Ulubione 
- Rekomendacje filmów podobnych do wybranego tytułu (KNN)  
- Pobieranie szczegółów filmu 
- Logowanie, rejestracja, zmiana ustawień konta użytkownika


---

## Struktura projektu
MovieManiac
    >app
        >static
            --recommender.js
            --sidebar.js
            --style.css
        >templates
            --base.html
            --dashboard.html
            --favorites.html
            --login.html
            --movie.html
            --movies-list.html
            --ranking.html
            --recommendations.html
            --register.html
            --search.html
            --settings.html
            --watched.html
        --__init__.py
        --auth.py
        --db_utils.py
        --recommender.py
        --routes.py
    --Dockerfile
    --main.py
    --movielens.db
    --README.md
    --requirements.txt
    >tests


