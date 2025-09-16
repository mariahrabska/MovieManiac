# app/__init__.py
from flask import Flask
from .routes import main
from .auth import auth


def create_app():
    app = Flask(__name__)
    app.secret_key = 'tajny_klucz'
    


    # rejestracja blueprintów
    app.register_blueprint(main)
    app.register_blueprint(auth)

    return app