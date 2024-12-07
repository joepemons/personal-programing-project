from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from config import CONFIG
from create_db_bikes import BikesDB
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'bikes123'

def get_db_connection():
    conn = sqlite3.connect(CONFIG["database"]["name"])
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('you need to login first.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def count_rows():
    try:
        with sqlite3.connect('bikes.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM bikes")
            rows = cur.fetchone()[0]
            print(f"Total rows in the table: {rows}")

    except sqlite3.Error as e:
        print("error", e)

@app.route('/')
def homepage():
    return render_template("homepage.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    elif request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        
        conn = get_db_connection()
        try:
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                         (username, password_hash))
            conn.commit()
        except sqlite3.IntegrityError:
            flash("Username already exists.")
            return redirect(url_for("register"))
        finally:
            conn.close()
        
        flash('Registration successful.')
        return redirect(url_for("login"))

@app.route("/login/", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    
    elif request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        try:
            user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            conn.close()

            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                #flash('Logged in successfully!')
                print(f"User logged in: {user['id']}")
                print(f"User id: {session['user_id']}")
                return redirect(url_for('overview'))
            else:
                flash('Invalid username or password.')
                return redirect(url_for('login'))
        except sqlite3.Error as e:
            flash(f"Database error: {e}")
            return redirect(url_for('login'))
        
@app.route('/overview')
@login_required
def overview():
    return render_template('overview.html')

@app.route('/bikes')
@login_required
def bikes():
    conn = get_db_connection()
    all_bikes = conn.execute('SELECT Brand, model, type, price, status, image_url FROM bikes').fetchall()
    conn.close()
    print(f"all bikes: {all_bikes}")
    return render_template("bikes.html", bikes=all_bikes)

@app.route('/rent', methods=["GET", "POST"])
@login_required
def rent():
    bike_id=request.args.get('bike_id', 0)
    bike_name=request.args.get('bike_name', '')
    bike_model=request.args.get('bike_model', '')
    bike_price=request.args.get('bike_price', 0)
    
    print(f"bike_id: {bike_id}")
    print(f"bike_name: {bike_name}")
    print(f"bike_model: {bike_model}")
    print(f"bike_price: {bike_price}")

    print(f"request.method: {request.method}")

    if request.method == "POST":
        user_id = session.get('user_id')
        print(f"user_id: {user_id}")
        if user_id:
            conn = get_db_connection()
            cursor = conn.cursor()

            start_date = request.form["start_date"]
            end_date = request.form["end_date"]

            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            nights = (end - start).days
            total_cost = nights * bike_price

            cursor.execute('INSERT INTO Reservations (bike_id, user_id, start_date, end_date, total_cost) VALUES (?, ?, ?, ?, ?)',
                           (bike_id, user_id, start_date, end_date, total_cost))
            print(f"Reservation added: {bike_id}, {user_id}, {start_date}, {end_date}, {total_cost}")
            reservation_id = cursor.lastrowid

            conn.execute('INSERT INTO transactions (reservation_id, is_paid, payment_date, due_date) VALUES (?, ?, ?, ?)',
                         (reservation_id, 'No', '', ''))
            conn.commit()
            conn.close()
            flash('Bike rented successfully!')
            return redirect(url_for('thank_you'))
        else:
            flash('You need to login first.')
            return redirect(url_for('login'))
    count_rows()
    return render_template("rent.html", bike_id=bike_id, bike_name=bike_name, bike_model=bike_model, bike_price=bike_price)

@app.route('/thank_you', methods=['GET'])
@login_required
def thank_you():
    return render_template("thank_you.html")


@app.route('/parts')
@login_required
def parts():
    conn = get_db_connection()
    all_parts = conn.execute('SELECT name, price FROM parts').fetchall()
    conn.close()
    print(f"all parts: {all_parts}")
    return render_template("parts.html", parts=all_parts)

@app.route("/logout/")
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully!')
    return redirect(url_for('homepage'))

if __name__ == "__main__":
    app.run(host=CONFIG["frontend"]["listen_ip"], port=CONFIG["frontend"]["port"], debug=CONFIG["frontend"]["debug"])