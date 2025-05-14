from flask import Flask, render_template, request, redirect, session, url_for
from datetime import datetime
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-key")
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Upewnij się, że folder na pliki istnieje
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 🔸 Tworzenie bazy danych (jeśli nie istnieje)
def init_db():
    with sqlite3.connect('orders.db') as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                email TEXT,
                phone TEXT,
                order_type TEXT,
                dimensions TEXT,
                qty TEXT,
                details TEXT,
                attachment TEXT,
                created_at TEXT,
                due_date TEXT
            )
        ''')
        conn.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        password TEXT
                    )
                ''')
@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with sqlite3.connect('orders.db') as conn:
            try:
                conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
                conn.commit()
                return redirect('/login')
            except sqlite3.IntegrityError:
                error = 'Nazwa użytkownika jest już zajęta.'

    return render_template('register.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with sqlite3.connect('orders.db') as conn:
            cursor = conn.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
            user = cursor.fetchone()

            if user:
                session['logged_in'] = True
                session['username'] = username
                return redirect('/')
            else:
                error = 'Nieprawidłowy login lub hasło'

    return render_template('login.html', error=error)

@app.route('/confirmation')
def confirmation():
    return render_template('confirmation.html')

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect('/login')
    return render_template('index.html', username=session.get('username'))

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    order_type = request.form['order_type']
    dimensions = request.form['dimensions']
    qty = request.form['qty']
    details = request.form['details']
    consent = request.form.get('consent')
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    due_date = request.form['due_date']

    if not consent:
        return "Musisz wyrazić zgodę na przetwarzanie danych osobowych", 400

    # Obsługa pliku
    file = request.files['attachment']
    filename = ''
    if file and file.filename:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

    # Zapis do bazy danych
    with sqlite3.connect('orders.db') as conn:
        conn.execute('''
            INSERT INTO orders (name, email, phone, order_type, dimensions, qty, details, attachment, created_at, due_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, email, phone, order_type, dimensions, qty, details, filename, created_at, due_date))

    return redirect('/confirmation')
@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect('/login')
    
    with sqlite3.connect('orders.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute('SELECT * FROM orders ORDER BY id DESC')
        orders = cursor.fetchall()
    return render_template('admin.html', orders=orders)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect('/')

    if not consent:
        return "Musisz wyrazić zgodę na przetwarzanie danych osobowych", 400

    # Obsługa pliku
    file = request.files['attachment']
    filename = ''
    if file and file.filename:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

    # Zapis do bazy danych
    with sqlite3.connect('orders.db') as conn:
        conn.execute('''
            INSERT INTO orders (name, email, phone, order_type, dimensions, qty, details, attachment)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, email, phone, order_type, dimensions, qty,  details, filename))

    return redirect('/confirmation')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)

