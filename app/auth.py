# auth.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os

auth = Blueprint('auth', __name__)
'''
def get_db_connection():
    conn = sqlite3.connect('movielens.db', timeout=10)  # baza danych
    conn.row_factory = sqlite3.Row
    return conn'''

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'movielens.db')


def get_db_connection():
    """Tworzy nowe, krótkotrwałe połączenie z bazą danych."""
    conn = sqlite3.connect(DATABASE_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


@auth.route('/')
def home():
    return redirect(url_for('auth.login'))

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            return redirect(url_for('main.dashboard'))
        else:
            flash('Incorrect email and/or password', 'error')

    return render_template('login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        errors = []

        if not username:
            errors.append('Username cannot be blank.')
        if '@' not in email or '.' not in email:
            errors.append('Email has to contain "@" and "."')
        if len(password) < 8:
            errors.append('Password has to be at least 8 characters long')

        conn = get_db_connection()
        if conn.execute('SELECT 1 FROM users WHERE email=?', (email,)).fetchone():
            errors.append('There is account with this email already.')
        if conn.execute('SELECT 1 FROM users WHERE username=?', (username,)).fetchone():
            errors.append('Username is taken. Pick another one.')

        if errors:
            for e in errors:
                flash(e, 'error')
            conn.close()
            return render_template('register.html')  # <-- nie redirect, tylko render

        # Dodanie użytkownika
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        conn.execute('INSERT INTO users (username,email,password) VALUES (?,?,?)',
                     (username,email,hashed_pw))
        conn.commit()
        conn.close()

        flash('Account is created! You can log in now.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')


@auth.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
