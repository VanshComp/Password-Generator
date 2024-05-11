import base64
from collections import Counter
from datetime import datetime
import os
import pickle
import json
from tkinter import messagebox
import cv2
import face_recognition
from flask import Flask, get_flashed_messages, jsonify, render_template, request, redirect, url_for,session,flash
from flask_sqlalchemy import SQLAlchemy 
import random
import string
import re
import sqlite3
import numpy as np

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db' 
app.config['SQLALCHEMY_DATABASE_MODIFIACTIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'
    
with app.app_context():
    db.create_all()

conn = sqlite3.connect('users.db')
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);
''')
conn.commit()
cursor.execute('SELECT * FROM user')
rows = cursor.fetchall()
for row in rows:
    print(row)
conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/Services')
def services():
    return render_template('service.html')

@app.route('/Generate')
def generate_page():
    return render_template('generate.html')

@app.route('/generate', methods=['POST'])
def generate():
    length = int(request.form['length'])
    include_numbers = True if request.form.get('numbers') else False
    include_symbols = True if request.form.get('symbols') else False

    chars = string.ascii_letters
    if include_numbers:
        chars += string.digits
    if include_symbols:
        chars += string.punctuation

    password = ''.join(random.choice(chars) for _ in range(length))
    return jsonify({'password': password})

@app.route('/Analyze')
def analyze_page():
    return render_template('analyzer.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    password = request.form['password']
    passwords_with_sites = [{'password': 'password1', 'site': 'site1.com'}, {'password': 'password2', 'site': 'site2.com'}]
    length_distribution, common_patterns, strength_analysis, password_usage = analyze_password(password, passwords_with_sites)
    return jsonify({
        'length_distribution': dict(length_distribution),
        'common_patterns': dict(common_patterns),
        'strength_analysis': strength_analysis,
        'password_usage': password_usage
    })

def analyze_password(password, passwords_with_sites):
    passwords = [entry['password'] for entry in passwords_with_sites]
    password_lengths = [len(password) for password in passwords]
    length_distribution = Counter(password_lengths)

    common_patterns = Counter()
    for pswd in passwords:
        patterns = re.findall(r'[a-zA-Z]+|\d+|[^a-zA-Z\d\s]', pswd)
        common_patterns.update(patterns)

    strength_analysis = {
        'lowercase_letters': any(c.islower() for c in password),
        'uppercase_letters': any(c.isupper() for c in password),
        'digits': any(c.isdigit() for c in password),
        'special_characters': any(not c.isalnum() for c in password),'common_words': sum(1 for pswd in passwords if pswd.lower() == password.lower()),
        'unique_passwords': len(set(passwords)),
    }

    password_usage = passwords.count(password)

    return length_distribution, common_patterns, strength_analysis, password_usage

@app.route('/Validate')
def validate_page():
    return render_template('validation.html', error=get_flashed_messages())

@app.route('/validate', methods=['POST'])
def validate():
    username = request.form['usrname']
    password = request.form['psw']

    if not os.path.exists('saved_passwords'):
        os.makedirs('saved_passwords')

    saved_credentials_file = 'saved_passwords/credentials.txt'

    if password_check(password):
        response = {'status': 'success', 'message': 'Password is valid'}
        with open(saved_credentials_file, 'a') as f:
            f.write(f"{username}:{password}\n")
    else:
        response = {'status': 'error', 'message': '''Password is invalid.
                    Check: Length should be at least 6
                    Password should have at least one numeral
                    Password should have at least one uppercase letter
                    Password should have at least one uppercase letter
                    Password should have at least one lowercase letter'''}

    return jsonify(response)
    
def password_check(passwd):
    SpecialSym =['$', '@', '#', '%']
    val = True

    if len(passwd) < 6:
        print('length should be at least 6')
        val = False

    if len(passwd) > 20:
        print('length should be not be greater than 20')
        val = False

    if not any(char.isdigit() for char in passwd):
        print('Password should have at least one numeral')
        val = False

    if not any(char.isupper() for char in passwd):
        print('Password should have at least one uppercase letter')
        val = False

    if not any(char.islower() for char in passwd):
        print('Password should have at least one lowercase letter')
        val = False

    if not any(char in SpecialSym for char in passwd):
        print('Password should have at least one of the symbols $@#%')
        val = False

    return val

@app.route('/face')
def face():
    return render_template('face_recognition.html')

@app.route('/save_photo', methods=['POST'])
def save_photo():
    photo_data = request.form.get('photo')
    photo_bytes = base64.b64decode(photo_data.split(',')[1])
    photo_filename = 'capture_photos/photo.jpg'
    if not os.path.exists('capture_photos'):
        os.makedirs('capture_photos')
    with open(photo_filename, 'wb') as photo_file:
        photo_file.write(photo_bytes)
    return jsonify({'success': True})

@app.route('/save_face_data', methods=['POST'])
def save_face_data():
    name = request.form['name']
    ref_id = request.form['ref_id']
    face_encoding = request.form['face_encoding']

    try:
        save_reference(name, ref_id, face_encoding)
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error saving face recognition data: {e}")
        return jsonify({'success': False})

def save_reference(name, ref_id, face_encoding):
    try:
        with open("ref_name.pkl", "rb") as f:
            ref_dict = pickle.load(f)
    except FileNotFoundError:
        ref_dict = {}

    ref_dict[ref_id] = name

    with open("ref_name.pkl", "wb") as f:
        pickle.dump(ref_dict, f)

def view_passwords(self):
    if self.passwords_with_sites:
        passwords_info = "\n".join([f"Site: {entry['site']}, Password: {entry['password']}" for entry in self.passwords_with_sites])
        messagebox.showinfo("Saved Passwords", passwords_info)
    else:
        messagebox.showinfo("No Passwords", "No passwords saved yet.")

def recognize_face():
    try:
        with open("ref_embed.pkl", "rb") as f:
            embed_dict = pickle.load(f)
    except FileNotFoundError:
        embed_dict = {}

    name = input("Enter your name: ")
    ref_id = input("Enter your ID: ")

    max_attempts = 3
    for attempt in range(max_attempts):
        webcam = cv2.VideoCapture(0)
        while True:
            check, frame = webcam.read()
            cv2.imshow("Recognizing", frame)
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = small_frame[:, :, ::-1]
            key = cv2.waitKey(1)
            if key == ord('s'):
                face_locations = face_recognition.face_locations(rgb_small_frame)
                if face_locations != []:
                    if not os.path.exists("captured_photos"):
                        os.makedirs("captured_photos")
                    photo_filename = f"{name}_{ref_id}.jpg"
                    photo_path = os.path.join("captured_photos", photo_filename)
                    cv2.imwrite(photo_path, frame)
                    face_encoding = face_recognition.face_encodings(frame)[0]
                    return face_encoding
            elif key == ord('q'):
                print("Turning off camera.")
                webcam.release()
                print("Camera off.")
                print("Program ended.")
                cv2.destroyAllWindows()
                return None
            elif key == ord('r'):
                print("Retaking photo...")
                break
        if attempt == max_attempts - 1:
            print("Maximum attempts reached.")
            return None

    print("Exceeded maximum attempts.")
    return None

if __name__ == '__main__':
    app.run(debug=True)