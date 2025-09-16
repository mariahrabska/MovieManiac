from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
'''

# main.py
from flask import Flask
from app.routes import main  # rekomendacje
from app.auth import auth    # logowanie/rejestracja

def create_app():
    app = Flask(__name__)
    app.secret_key = 'tajny_klucz'  # zmień na coś bezpiecznego w produkcji

    # Rejestracja blueprintów
    app.register_blueprint(main)
    app.register_blueprint(auth)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)'''
