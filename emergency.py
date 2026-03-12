# Standard library imports
import os
import json
import secrets
import logging   
import uuid
from datetime import datetime, timedelta
from functools import wraps
from urllib.request import urlopen
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Flask and related extensions
from flask import (
    Flask, 
    render_template, 
    request, 
    flash, 
    redirect, 
    url_for, 
    session,
    current_app,
    send_from_directory,
    jsonify
)
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

# Security related imports
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Database
import sqlite3

# Email handling
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Data processing
import pandas as pd
import numpy as np
import joblib

# External services
import requests
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException





  
alert_data=[]

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Email configuration with environment variables
class EmailConfig:
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
    SENDER_EMAIL = os.environ.get('SENDER_EMAIL')
    DOMAIN = os.environ.get('DOMAIN', 'http://localhost:5000')
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(16))



def init_db():
    """Initialize the database with necessary tables"""
    conn = sqlite3.connect('user_database.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Password reset tokens table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS password_reset_tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        token TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        used BOOLEAN DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    conn.commit()
    conn.close()


def test_email_configuration():
    """Test email configuration and return detailed status"""
    try:
        server = smtplib.SMTP(EmailConfig.SMTP_SERVER, EmailConfig.SMTP_PORT)
        server.set_debuglevel(1)  # Enable debug output
        logger.info("SMTP connection established")
        
        # Start TLS
        server.starttls()
        logger.info("TLS started")
        
        # Test login
        server.login(EmailConfig.SMTP_USERNAME, EmailConfig.SMTP_PASSWORD)
        logger.info("SMTP login successful")
        
        server.quit()
        return True, "Email configuration is correct"
    except Exception as e:
        logger.error(f"Email configuration test failed: {str(e)}")
        return False, str(e)

def send_reset_email(email, reset_token):
    """Send password reset email to user with enhanced error handling and logging"""
    reset_link = f"{EmailConfig.DOMAIN}/reset-password/{reset_token}"
    
    # Log the attempt
    logger.info(f"Attempting to send reset email to {email}")
    logger.debug(f"Reset link generated: {reset_link}")
    
    msg = MIMEMultipart()
    msg['From'] = EmailConfig.SENDER_EMAIL
    msg['To'] = email
    msg['Subject'] = "Password Reset Request"
    
    body = f"""
    Hello,
    
    You have requested to reset your password. Please click the link below to reset your password:
    
    {reset_link}
    
    This link will expire in 24 hours.
    Time requested: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    
    If you did not request this password reset, please ignore this email.
    
    Best regards,
    Your Application Team
    """
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        # Create SMTP connection with debugging
        server = smtplib.SMTP(EmailConfig.SMTP_SERVER, EmailConfig.SMTP_PORT)
        server.set_debuglevel(1)  # Enable debugging
        
        # Log connection attempt
        logger.info("Establishing SMTP connection")
        
        server.starttls()
        logger.info("TLS started")
        
        # Attempt login
        server.login(EmailConfig.SMTP_USERNAME, EmailConfig.SMTP_PASSWORD)
        logger.info("SMTP login successful")
        
        # Send email
        server.send_message(msg)
        logger.info(f"Reset email sent successfully to {email}")
        
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication Error: {str(e)}")
        raise Exception("Email server authentication failed. Check username and password.")
        
    except smtplib.SMTPException as e:
        logger.error(f"SMTP Error: {str(e)}")
        raise Exception(f"SMTP error occurred: {str(e)}")
        
    except Exception as e:
        logger.error(f"Unexpected error sending email: {str(e)}")
        raise Exception(f"Failed to send email: {str(e)}")
    
    

# flood_model = joblib.load(r'C:\Users\USER\Desktop\arun\pro\rainfall.pkl')
# landslide_model = joblib.load(r'C:\Users\USER\Desktop\arun\pro\landslidee.pkl')
# earthquack_model = joblib.load(r'C:\Users\USER\Desktop\arun\pro\earthquack_model.pkl')
# tornadoes_model = joblib.load(r"C:\Users\USER\Desktop\arun\pro\tornadoes.pkl")
# tsunami_model = joblib.load(r'C:\Users\USER\Desktop\arun\pro\random_forest_tsunami_model.pkl')

flood_model = joblib.load(r"E:\WEATHER_PREDICITION\disaster_prediciton\rainfall.pkl")
landslide_model = joblib.load(r"E:\WEATHER_PREDICITION\disaster_prediciton\landslidee .pkl")
earthquack_model = joblib.load(r"E:\WEATHER_PREDICITION\disaster_prediciton\earthquack_model.pkl")
tornadoes_model = joblib.load(r"E:\WEATHER_PREDICITION\disaster_prediciton\tornadoes.pkl")
tsunami_model = joblib.load(r"E:\WEATHER_PREDICITION\disaster_prediciton\random_forest_tsunami_model.pkl")


# Helper functions (same as before)
def get_weather_data(location, start_date, end_date, api_key):
    base_url = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"
    params = {
        "elements": "datetime,temp,tempmax,tempmin,precip,windspeed,feelslike,pressure",
        "include": "fcst,obs,histfcst,stats",
        "key": api_key,
        "contentType": "json"
    }
    
    url = f"{base_url}/{location}/{start_date}/{end_date}"
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data['days'])
        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)
        return df
    else:
        print(f"Error: Unable to fetch data. Status code: {response.status_code}")
        return None

def calculate_total_rainfall(weather_data):
    if weather_data is not None and 'precip' in weather_data.columns:
        total_rainfall = weather_data['precip'].sum()
        return total_rainfall
    else:
        return None

def get_elevation_with_retry(lat, lon, retries=3, delay=2):
    url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}"
    
    try:
            url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}"
            response = requests.get(url)
            
            if response.status_code == 200:
                elevation_data = response.json()
                if 'results' in elevation_data and len(elevation_data['results']) > 0:
                    return elevation_data['results'][0]['elevation']
            # If the response is not as expected or no results found, return None 
            return None
    except:
            # Return None silently in case of any exceptions or errors
            return None # Return None if all attempts fail

shared_data = {}
app.secret_key = "1234"

@app.route('/')

def home():
    # if 'username' in session:
    WEATHER_API_KEY = os.environ.get('WEATHER_API_KEY')
    WEATHER_BASE_URL = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"
    GEOCODING_URL = "https://nominatim.openstreetmap.org/reverse"

    # Default coordinates for Trivandrum (or any default location)
    default_lat = 8.5241
    default_lon = 76.9366
    
    # Get coordinates from query parameters or use defaults
    lat = request.args.get('lat', default_lat)
    lon = request.args.get('lon', default_lon)
    
    """Get location name from coordinates using Nominatim"""

    headers = {
        'User-Agent': 'WeatherApp/1.0'
    }
    params = {
        'lat': lat,
        'lon': lon,
        'format': 'json',
        'zoom': 10
    }
    response = requests.get(GEOCODING_URL, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()
    
    address = data.get('address', {})
    city = address.get('city') or address.get('town') or address.get('village') or address.get('suburb')
    state = address.get('state')
    country = address.get('country')
    place=address.get('village')

    location = f"{lat},{lon}"
    url = f"{WEATHER_BASE_URL}/{location}?unitGroup=metric&key={WEATHER_API_KEY}&contentType=json"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    
    current = data.get('currentConditions', {})
    temperature= round(current.get('temp', 0))


    humidity= current.get('humidity', 0)
    wind_speed= round(current.get('windspeed', 0))
    last_updated= datetime.fromtimestamp(current.get('datetimeEpoch', 0)).strftime('%H:%M')
    date= datetime.now().strftime('%d/%m/%Y')

    # Process weather condition for icon selection
    condition = current.get('conditions', '').lower()
    def weather(condition):
        if 'rain' in condition:
            return 'fas fa-cloud-rain'
        elif 'cloud' in condition:
            return 'fas fa-cloud'
        elif 'clear' in condition or 'sunny' in condition:
            return 'fas fa-sun'
        elif 'snow' in condition:
            return 'fas fa-snowflake'
        elif 'fog' in condition or 'mist' in condition:
            return 'fas fa-smog'
        elif 'wind' in condition:
            return 'fas fa-wind'
        return 'fas fa-cloud' 
    
    context={
    'temperature': temperature,
    'condition': condition,
    'icon_class': weather(condition),
    'humidity': humidity,
    'wind_speed': wind_speed,
    'location': city,
    'last_updated': last_updated,
    'date': date,}
    url = "http://ipinfo.io/json"
    response = urlopen(url)
    data = json.load(response)

    # Get weather data
    location = data["loc"]  # Latitude and longitude (e.g., "10.8505,76.2711")
    api_key = os.environ.get('WEATHER_API_KEY')
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d')

    weather_data = get_weather_data(location, start_date, end_date, api_key)
    if weather_data is not None:
    # Get rainfall data for the latest date
        last_date_data = weather_data.iloc[-1]  # Gets the last row in the DataFrame
        today_rain = last_date_data['precip'] if 'precip' in last_date_data else None
    today_rain=today_rain*100
    today_rain=round(today_rain, 2)    
    if weather_data is not None:
        total_rainfall = calculate_total_rainfall(weather_data)
    rain = total_rainfall * 100

    # Split latitude and longitude
    lat, lon = map(float, data["loc"].split(','))

    # Flood prediction
    flood_data = np.array([[lat, lon, rain]])
    flood_pred = flood_model.predict(flood_data)
    flood_result = "  Flood Predict" if flood_pred[0] == 1 else "No Flood"

    # Get elevation data
    alt = get_elevation_with_retry(lat, lon)
    alt = alt if alt is not None else 235.0

    # Landslide prediction
    landslide_data = np.array([[lat, lon, alt, rain]])
    landslide_pred = landslide_model.predict(landslide_data)
    landslide_result = "Landslide Predict" if landslide_pred[0] == 1 else "No Landslide"

    # Earthquake prediction
    dep = 50
    earthquake_mag = np.round(earthquack_model.predict(np.array([[lat, lon, dep]]))[0])
    """------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"""
    """------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"""
    earthquake_mag=9
    """------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"""
    """------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"""
    if earthquake_mag <= 4:
        earthquake_result = "magnitude",earthquake_mag,"No risk"
    elif 4 < earthquake_mag <= 6:
        earthquake_result = "magnitude",earthquake_mag,"Low risk"
    elif 6 < earthquake_mag <= 8:
        earthquake_result = "magnitude", earthquake_mag, "Moderate risk"
    elif 8 < earthquake_mag <= 9:
        earthquake_result = "magnitude", earthquake_mag, "High risk"
    else:
        earthquake_result = "magnitude", earthquake_mag, "Very high risk"

    # Tornado prediction
    win = weather_data["windspeed"][-1]
    ln = 15.5
    today = datetime.today()
    tornado_data = np.array([[today.year, today.month, today.day, lat, lon, ln, win]])
    tornado_pred = tornadoes_model.predict(tornado_data)
    tornado_results = [
        "No Cyclone", "Light Cyclone", "Moderate Cyclone",
        "Considerable Cyclone", "Severe Cyclone", "Incredible Cyclone"
    ]
    tornado_result = tornado_results[tornado_pred[0]]

    # Tsunami prediction
    reg = 8
    dep = 100
    tsunami_data = np.array([[today.year, today.month, today.day, lat, lon, reg, dep]])
    tsunami_pred = tsunami_model.predict(tsunami_data)
    tsunami_pred[0]-=1
    """------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"""
    """------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"""
    # tsunami_pred[0]+=3
    """------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"""
    """------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"""
    # tsunami_result = "magnitude",round(tsunami_pred[0], 1), "No tsunami" if tsunami_pred[0] < 8 elif "magnitude",round(tsunami_pred[0], 1), "Predict tsunami"
    if tsunami_pred[0] <= 6.9:
        tsunami_result = "magnitude",round(tsunami_pred[0],1),"No risk"
    elif 6.9 < earthquake_mag <= 7.9:
        tsunami_result = "magnitude",round(tsunami_pred[0],1),"Tsunami Warning"
    elif  tsunami_pred[0] > 7.9:
        tsunami_result = "magnitude",round(tsunami_pred[0],1), "Tsunami Alert"
    shared_data['flood_result'] = flood_result
    shared_data['landslide_result'] = landslide_result
    shared_data['earthquake_result'] = earthquake_result
    shared_data['tornado_result'] = tornado_result
    shared_data['tsunami_result'] = tsunami_result
    shared_data['today_rain'] = today_rain
    # def alertmessage(flood_result,landslide_result,earthquake_result,tornado_result,tsunami_result,today_rain):
    #     return flood_result,landslide_result,earthquake_result,tornado_result,tsunami_result,today_rain
    return render_template('index.html',data=context,flood_result=flood_result,
                            landslide_result=landslide_result,
                            earthquake_result=earthquake_result,
                            tornado_result=tornado_result,
                            tsunami_result=tsunami_result,
                            today_rain=today_rain,
                            mapbox_token=os.environ.get('MAPBOX_ACCESS_TOKEN'))

@app.route('/SignUp', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        confirmPassword = request.form['confirmPassword']
        
        # Validate passwords match
        if password != confirmPassword:
            flash('Passwords do not match!', 'danger')
            return render_template('SignUp.html')
        
        # Check all fields are filled
        if not all([username, email, phone, password, confirmPassword]):
            flash('All fields are required', 'error')
            return render_template('SignUp.html')
        
        # Validate password
        is_valid, message = validate_password(password)
        if not is_valid:
            flash(message, 'error')
            return render_template('SignUp.html')
        
        # Hash the password
        hashed_password = generate_password_hash(password)
        
        try:
            conn = sqlite3.connect('user_database.db')
            cursor = conn.cursor()
            
            # Insert user
            cursor.execute('''
                INSERT INTO users (username, email, phone, password) 
                VALUES (?, ?, ?, ?)
            ''', (username, email, phone, hashed_password))
            
            conn.commit()
            flash('Registration successful! Please login.', 'success')
        except sqlite3.IntegrityError:
            flash('Email or phone number already exists', 'error')
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
        finally:
            conn.close()
    
    return render_template('SignUp.html')

# Password validation function
def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"

@app.route('/signin', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = sqlite3.connect('user_database.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, email, password,username FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[3]
            flash('Login successful!', 'success')

            return redirect(url_for('home'))  

        else:
            flash('Invalid email or password', 'error')
            
    return render_template('SignIn.html')

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)






@app.route('/Signout')
def logout():
# Remove chat_joined from session

    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return render_template('SignIn.html')




ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

# Decorator to ensure admin authentication
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Please login as admin to access this page.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Admin login route
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            flash('Welcome, Admin!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('admin/login.html')

# Admin logout route
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('base'))

# Admin dashboard route with all user data
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    conn = sqlite3.connect('user_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
    users = cursor.fetchall()
    conn.close()

    return render_template('admin/base.html', users=users)

# Admin view users route
@app.route('/admin/users')
@admin_required
def admin_users():
    conn = sqlite3.connect('user_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
    users = cursor.fetchall()
    conn.close()
    
    return render_template('admin/users.html', users=users)

# Admin edit user route
@app.route('/admin/user/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_user(user_id):
    conn = sqlite3.connect('user_database.db')
    cursor = conn.cursor()
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        
        try:
            cursor.execute('''
                UPDATE users 
                SET username = ?, email = ?
                WHERE id = ?
            ''', (username, email, user_id))
            conn.commit()
            flash('User updated successfully', 'success')
            return redirect(url_for('admin_users'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists', 'error')
    
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user is None:
        flash('User not found', 'error')
        return redirect(url_for('admin_users'))
    
    return render_template('admin/edit_user.html', user=user)

# Admin delete user route
@app.route('/admin/user/delete/<int:user_id>', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    conn = sqlite3.connect('user_database.db')
    cursor = conn.cursor()
    
    try:
        # Delete associated reset tokens first
        cursor.execute('DELETE FROM password_reset_tokens WHERE user_id = ?', (user_id,))
        # Then delete the user
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        flash('User deleted successfully', 'success')
    except sqlite3.Error as e:
        flash(f'Error deleting user: {str(e)}', 'error')
    
    conn.close()
    return redirect(url_for('admin_users'))

# Admin search users route
@app.route('/admin/search', methods=['GET'])
@admin_required
def admin_search():
    query = request.args.get('q', '')
    
    conn = sqlite3.connect('user_database.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM users 
        WHERE username LIKE ? OR email LIKE ?
        ORDER BY created_at DESC
    ''', (f'%{query}%', f'%{query}%'))
    
    users = cursor.fetchall()
    conn.close()
    
    return render_template('admin/users.html', users=users, search_query=query)

# Initialize the database
def init_db():
    conn = sqlite3.connect('user_database.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Password reset tokens table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS password_reset_tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        token TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        used BOOLEAN DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    conn.commit()
    conn.close()
    
    
    
    
    
    
    
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload size

CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Create the folder if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

messages = []




@app.route('/uploads/<path:filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/upload_file', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({
            'username': request.form['username'],
            'filename': filename,
            'originalFilename': file.filename
        })

@app.route('/upload_voice', methods=['POST'])
def upload_voice():
    if 'voice' not in request.files:
        return jsonify({'error': 'No voice part'}), 400
    voice_file = request.files['voice']
    if voice_file.filename == '':
        return jsonify({'error': 'No selected voice file'}), 400
    if voice_file:
        filename = secure_filename(f"{uuid.uuid4()}.wav")
        voice_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({
            'username': request.form['username'],
            'filename': filename
        })

@socketio.on('connect')
def handle_connect():
    emit('chat_history', messages)

@socketio.on('send_message')
def handle_message(data):
    message = {
        'id': str(uuid.uuid4()),
        'user': data['username'],
        'text': data['message'],
        'timestamp': datetime.now().strftime('%I:%M %p'),
        'type': 'text'
    }
    messages.append(message)
    emit('new_message', message, broadcast=True)

@socketio.on('send_file')
def handle_file(data):
    message = {
        'id': str(uuid.uuid4()),
        'user': data['username'],
        'filename': data['filename'],
        'originalFilename': data['originalFilename'],
        'timestamp': datetime.now().strftime('%I:%M %p'),
        'type': 'file'
    }
    messages.append(message)
    emit('new_message', message, broadcast=True)

@socketio.on('send_voice')
def handle_voice(data):
    message = {
        'id': str(uuid.uuid4()),
        'user': data['username'],
        'filename': data['filename'],
        'timestamp': datetime.now().strftime('%I:%M %p'),
        'type': 'voice'
    }
    messages.append(message)
    emit('new_message', message, broadcast=True)

@socketio.on('send_location')
def handle_location(data):
    message = {
        'id': str(uuid.uuid4()),
        'user': data['username'],
        'latitude': data['latitude'],
        'longitude': data['longitude'],
        'timestamp': datetime.now().strftime('%I:%M %p'),
        'type': 'location'
    }
    messages.append(message)
    emit('new_message', message, broadcast=True)

@socketio.on('delete_message')
def handle_delete_message(data):
    message_id = data['messageId']
    global messages

    # Find and remove the message by its ID
    messages = [msg for msg in messages if msg['id'] != message_id]

    # Notify all clients to remove the message from their UI
    emit('message_deleted', {'messageId': message_id}, broadcast=True)

    
    
CORS(app)

# Database Configuration


# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///emergency.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Twilio Configuration (Loaded from .env)
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_FROM_NUMBER = os.getenv('TWILIO_FROM_NUMBER')

# Database Model
class EmergencyContact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone
        }

# Emergency SMS Sending Route
@app.route('/send_emergency_sms', methods=['POST'])
def send_emergency_sms():
    try:
        # Check for emergency conditions (you can customize this part)
        flood_result = shared_data.get('flood_result')
        landslide_result = shared_data.get('landslide_result')
        earthquake_result = shared_data.get('earthquake_result')
        tornado_result = shared_data.get('tornado_result')
        tsunami_result = shared_data.get('tsunami_result')
        # Check if any emergency condition is true
        alert_messages = []
        
        if flood_result == "Flood Predict":
            alert_messages.append("🌊 Flood Warning")
        
        if earthquake_result and earthquake_result[1] > 6:
            alert_messages.append(f"🌍 Earthquake Risk: Magnitude {earthquake_result[1]}")
        
        if tsunami_result and tsunami_result[1] > 6.9:
            alert_messages.append(f"🌊 Tsunami Warning: Magnitude {tsunami_result[1]}")
        
        if landslide_result == "Landslide Predict":
            alert_messages.append("⛰️ Landslide Warning")
        
        if tornado_result == "Considerable Cyclone" or tornado_result in [
            "Severe Cyclone",
            "Incredible Cyclone"
        ]:
            alert_messages.append(f"🌪️ Cyclone Alert: {tornado_result}")
        
        # If no alerts, return a response indicating no need to send SMS
        if not alert_messages:
            return jsonify({'message': 'No emergency conditions detected. No SMS sent.'}), 200

        # Get all contacts
        contacts = EmergencyContact.query.all()

        if not contacts:
            return jsonify({'error': 'No emergency contacts found'}), 400

        # Initialize Twilio client
        try:
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        except Exception as e:
            return jsonify({
                'error': 'Failed to initialize Twilio client',
                'details': str(e)
            }), 500

        successful_messages = []
        failed_messages = []

        # Send SMS to each contact
        for contact in contacts:
            try:
                # Ensure phone number is in E.164 format
                phone_number = contact.phone
                if not phone_number.startswith('+'):
                    phone_number = '+1' + phone_number.lstrip('0')  # Adjust country code as needed

                # Send SMS
                message = client.messages.create(
                    body="\n".join(alert_messages),
                    from_=TWILIO_FROM_NUMBER,
                    to=phone_number
                )
                successful_messages.append(contact.name)
                print(f"SMS sent successfully to {contact.name} at {phone_number}")
            except TwilioRestException as e:
                failed_messages.append(contact.name)
                print(f"Twilio Error sending SMS to {contact.name}: {str(e)}")
            except Exception as e:
                failed_messages.append(contact.name)
                print(f"General Error sending SMS to {contact.name}: {str(e)}")

        # Prepare response
        response = {
            'message': 'Emergency SMS process completed',
            'successful_contacts': successful_messages,
            'failed_contacts': failed_messages
        }

        return jsonify(response), 200

    except Exception as e:
        print(f"General error in emergency SMS: {str(e)}")
        return jsonify({'error': 'Failed to send emergency SMS', 'details': str(e)}), 500

# Add Contact Route
@app.route('/add_contact', methods=['POST'])
def add_contact():
    try:
        data = request.get_json()
        name = data.get('name')
        phone = data.get('phone')

        if not name or not phone:
            return jsonify({'error': 'Name and phone are required'}), 400

        # Validate phone number (basic validation)
        if not phone.startswith('+') and not phone.isdigit():
            return jsonify({'error': 'Invalid phone number format'}), 400

        # Save contact to database
        new_contact = EmergencyContact(name=name, phone=phone)
        db.session.add(new_contact)
        db.session.commit()

        return jsonify({'message': 'Contact added successfully', 'contact': new_contact.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        print(f"Error adding contact: {str(e)}")
        return jsonify({'error': 'Failed to add contact', 'details': str(e)}), 500

# Get Contacts Route
@app.route('/get_contacts', methods=['GET'])
def get_contacts():
    try:
        contacts = EmergencyContact.query.all()
        return jsonify([contact.to_dict() for contact in contacts]), 200
    except Exception as e:
        print(f"Error fetching contacts: {str(e)}")
        return jsonify({'error': 'Failed to fetch contacts', 'details': str(e)}), 500

# Delete Contact Route
@app.route('/delete_contact/<int:contact_id>', methods=['DELETE'])
def delete_contact(contact_id):
    try:
        contact = EmergencyContact.query.get(contact_id)
        if not contact:
            return jsonify({'error': 'Contact not found'}), 404

        db.session.delete(contact)
        db.session.commit()

        return jsonify({'message': 'Contact deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting contact: {str(e)}")
        return jsonify({'error': 'Failed to delete contact', 'details': str(e)}), 500



# Rest of your existing routes remain the same
@app.route('/Sos')
def sos():
    return render_template("sos.html")


@app.route('/map')
def mapp():
    
    return render_template("map.html")
    


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    init_db()
    app.run(debug=True)
    socketio.run(app, debug=True)


     