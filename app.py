import os
import sqlite3
import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "development_secret_key")

# Database setup
DATABASE = 'sitin_monitoring.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

# Create tables if they don't exist
def create_tables():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_number TEXT UNIQUE NOT NULL,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        middle_name TEXT,
        email TEXT UNIQUE NOT NULL,
        course TEXT NOT NULL,
        level TEXT NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        profile_pic TEXT
    )
    ''')
    
    # Create announcements table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS announcements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        posted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create feedback table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        laboratory TEXT NOT NULL,
        rating INTEGER NOT NULL,
        message TEXT,
        submitted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Create reservations table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reservations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        laboratory TEXT NOT NULL,
        purpose TEXT NOT NULL,
        reservation_date TEXT NOT NULL,
        time_slot TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Insert some initial announcements if none exist
    cursor.execute("SELECT COUNT(*) FROM announcements")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
        INSERT INTO announcements (title, content)
        VALUES 
        ('System Maintenance', 'The laboratory system will be under maintenance this weekend.'),
        ('Welcome to the Sit-In Monitoring System', 'Please make sure to follow all laboratory rules and guidelines')
        ''')
    
    conn.commit()
    conn.close()

# Call create_tables function
create_tables()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Helper function to get user by ID
def get_user(user_id):
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    return user

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        id_number = request.form['id_number']
        first_name = request.form['first_name']
        middle_name = request.form.get('middle_name', '')
        last_name = request.form['last_name']
        email = request.form['email']
        course = request.form['course']
        level = request.form['level']
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Validate password match
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('register'))
        
        # Hash the password
        hashed_password = generate_password_hash(password)
        
        db = get_db()
        
        # Check if ID number, email or username already exists
        existing_user = db.execute('SELECT * FROM users WHERE id_number = ? OR email = ? OR username = ?', 
                                 (id_number, email, username)).fetchone()
        
        if existing_user:
            flash('ID number, email or username already registered', 'danger')
            return redirect(url_for('register'))
        
        # Insert new user
        try:
            db.execute('''
            INSERT INTO users (id_number, first_name, middle_name, last_name, email, course, level, username, password, profile_pic)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (id_number, first_name, middle_name, last_name, email, course, level, username, hashed_password, None))
            db.commit()
            
            flash('Registration successful! You can now log in', 'success')
            return redirect(url_for('login'))
        except sqlite3.Error as e:
            flash(f'Registration failed: {str(e)}', 'danger')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    user = get_user(session['user_id'])
    
    db = get_db()
    announcements = db.execute('SELECT * FROM announcements ORDER BY posted_date DESC').fetchall()
    
    return render_template('dashboard.html', user=user, announcements=announcements)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user = get_user(session['user_id'])
    
    if request.method == 'POST':
        first_name = request.form['first_name']
        middle_name = request.form.get('middle_name', '')
        last_name = request.form['last_name']
        email = request.form['email']
        course = request.form['course']
        level = request.form['level']
        username = request.form['username']
        
        db = get_db()
        
        # Check if the username was changed and already exists
        if username != user['username']:
            existing_user = db.execute('SELECT * FROM users WHERE username = ? AND id != ?', 
                                 (username, session['user_id'])).fetchone()
            if existing_user:
                flash('Username already taken', 'danger')
                return redirect(url_for('edit_profile'))
                
        # Check if email was changed and already exists
        if email != user['email']:
            existing_user = db.execute('SELECT * FROM users WHERE email = ? AND id != ?', 
                                 (email, session['user_id'])).fetchone()
            if existing_user:
                flash('Email already registered', 'danger')
                return redirect(url_for('edit_profile'))
        
        # Handle profile picture upload
        profile_pic_path = user['profile_pic']  # Default to current picture
        if 'profile_pic' in request.files and request.files['profile_pic'].filename != '':
            profile_pic = request.files['profile_pic']
            
            # Ensure static/uploads directory exists
            upload_dir = os.path.join(app.static_folder, 'uploads')
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            
            # Secure the filename and save the file
            filename = secure_filename(f"{session['user_id']}_{profile_pic.filename}")
            file_path = os.path.join(upload_dir, filename)
            profile_pic.save(file_path)
            
            # Update profile picture path in DB (store relative path from static folder)
            profile_pic_path = f"uploads/{filename}"
        
        # Update user information
        db.execute('''
        UPDATE users 
        SET first_name = ?, middle_name = ?, last_name = ?, email = ?, course = ?, level = ?, username = ?, profile_pic = ?
        WHERE id = ?
        ''', (first_name, middle_name, last_name, email, course, level, username, profile_pic_path, session['user_id']))
        db.commit()
        
        flash('Profile updated successfully', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('edit_profile.html', user=user)

@app.route('/feedback', methods=['POST'])
@login_required
def submit_feedback():
    laboratory = request.form['laboratory']
    rating = request.form['rating']
    message = request.form['message']
    
    db = get_db()
    
    # Insert feedback
    db.execute('''
    INSERT INTO feedback (user_id, laboratory, rating, message)
    VALUES (?, ?, ?, ?)
    ''', (session['user_id'], laboratory, rating, message))
    db.commit()
    
    flash('Feedback submitted successfully', 'success')
    return redirect(url_for('dashboard'))

@app.route('/reservation')
@login_required
def reservation():
    user = get_user(session['user_id'])
    
    # Get current month and year for the calendar
    now = datetime.datetime.now()
    month = now.month
    year = now.year
    
    # For demo purposes, we'll set available labs and times
    laboratories = ['524', '526', '542', '528', 'Mac']
    purposes = ['Python', 'Java programming', 'JavaScript', 'C++', 'C#', 'PHP', 'Ruby', 'Other']
    time_slots = ['8:00 AM', '9:00 AM', '10:00 AM', '11:00 AM', '12:00 PM', 
                  '1:00 PM', '2:00 PM', '3:00 PM', '4:00 PM', '5:00 PM']
    
    # Get calendar days for the current month
    first_day = datetime.date(year, month, 1)
    num_days = (datetime.date(year, month + 1, 1) - first_day).days if month < 12 else (datetime.date(year + 1, 1, 1) - first_day).days
    
    calendar_days = []
    for i in range(1, num_days + 1):
        calendar_days.append(datetime.date(year, month, i))
    
    # Get user's existing reservations
    db = get_db()
    user_reservations = db.execute('''
    SELECT * FROM reservations 
    WHERE user_id = ? 
    ORDER BY reservation_date
    ''', (session['user_id'],)).fetchall()
    
    return render_template('reservation.html', 
                          user=user, 
                          laboratories=laboratories,
                          purposes=purposes,
                          time_slots=time_slots,
                          calendar_days=calendar_days,
                          current_month=now.strftime('%B %Y'),
                          user_reservations=user_reservations)

@app.route('/book_reservation', methods=['POST'])
@login_required
def book_reservation():
    purpose = request.form['purpose']
    laboratory = request.form['laboratory']
    date = request.form['date']
    time_slot = request.form['time_slot']
    
    if not all([purpose, laboratory, date, time_slot]):
        flash('Please fill all reservation fields', 'danger')
        return redirect(url_for('reservation'))
    
    db = get_db()
    
    # Check if the slot is already booked
    existing = db.execute('''
    SELECT * FROM reservations 
    WHERE laboratory = ? AND reservation_date = ? AND time_slot = ?
    ''', (laboratory, date, time_slot)).fetchone()
    
    if existing:
        flash('This time slot is already booked. Please select another.', 'danger')
        return redirect(url_for('reservation'))
    
    # Insert reservation
    db.execute('''
    INSERT INTO reservations (user_id, laboratory, purpose, reservation_date, time_slot)
    VALUES (?, ?, ?, ?, ?)
    ''', (session['user_id'], laboratory, purpose, date, time_slot))
    db.commit()
    
    flash('Reservation booked successfully', 'success')
    return redirect(url_for('reservation'))

@app.route('/edit_reservation/<int:reservation_id>', methods=['GET', 'POST'])
@login_required
def edit_reservation(reservation_id):
    user = get_user(session['user_id'])
    
    db = get_db()
    
    # Get the reservation details
    reservation = db.execute('SELECT * FROM reservations WHERE id = ? AND user_id = ?', 
                           (reservation_id, session['user_id'])).fetchone()
    
    if not reservation:
        flash('Reservation not found or you do not have permission to edit it', 'danger')
        return redirect(url_for('reservation'))
    
    # For demo purposes, we'll set available labs and times
    laboratories = ['524', '526', '542', '528', 'Mac']
    purposes = ['Python', 'Java programming', 'JavaScript', 'C++', 'C#', 'PHP', 'Ruby', 'Other']
    time_slots = ['8:00 AM', '9:00 AM', '10:00 AM', '11:00 AM', '12:00 PM', 
                  '1:00 PM', '2:00 PM', '3:00 PM', '4:00 PM', '5:00 PM']
    
    if request.method == 'POST':
        purpose = request.form['purpose']
        laboratory = request.form['laboratory']
        date = request.form['date']
        time_slot = request.form['time_slot']
        
        if not all([purpose, laboratory, date, time_slot]):
            flash('Please fill all reservation fields', 'danger')
            return redirect(url_for('edit_reservation', reservation_id=reservation_id))
        
        # Check if the slot is already booked by someone else
        existing = db.execute('''
        SELECT * FROM reservations 
        WHERE laboratory = ? AND reservation_date = ? AND time_slot = ? AND id != ?
        ''', (laboratory, date, time_slot, reservation_id)).fetchone()
        
        if existing:
            flash('This time slot is already booked. Please select another.', 'danger')
            return redirect(url_for('edit_reservation', reservation_id=reservation_id))
        
        # Update reservation
        db.execute('''
        UPDATE reservations 
        SET laboratory = ?, purpose = ?, reservation_date = ?, time_slot = ?
        WHERE id = ? AND user_id = ?
        ''', (laboratory, purpose, date, time_slot, reservation_id, session['user_id']))
        db.commit()
        
        flash('Reservation updated successfully', 'success')
        return redirect(url_for('reservation'))
    
    return render_template('edit_reservation.html', 
                          user=user,
                          reservation=reservation,
                          laboratories=laboratories,
                          purposes=purposes,
                          time_slots=time_slots)

@app.route('/delete_reservation/<int:reservation_id>', methods=['POST'])
@login_required
def delete_reservation(reservation_id):
    db = get_db()
    
    # Check if the reservation belongs to the user
    reservation = db.execute('SELECT * FROM reservations WHERE id = ? AND user_id = ?', 
                           (reservation_id, session['user_id'])).fetchone()
    
    if not reservation:
        flash('Reservation not found or you do not have permission to delete it', 'danger')
        return redirect(url_for('reservation'))
    
    # Delete the reservation
    db.execute('DELETE FROM reservations WHERE id = ?', (reservation_id,))
    db.commit()
    
    flash('Reservation deleted successfully', 'success')
    return redirect(url_for('reservation'))

@app.route('/rules')
@login_required
def rules():
    user = get_user(session['user_id'])
    return render_template('rules.html', user=user)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
