from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import numpy as np
import joblib
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json
import os
from werkzeug.utils import secure_filename
import pandas as pd

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Load model
model = joblib.load('health_risk_model.pkl')

# Mappings
yes_no_map = {'Yes': 1, 'No': 0}
gender_map = {'Male': 0, 'Female': 1}
alcohol_map = {'None': 0, 'Moderate': 1, 'High': 2}
diet_map = {'High-Sugar': 0, 'High-Protein': 1, 'Balanced': 2}
pollution_map = {'Low': 0, 'Medium': 1, 'High': 2}
noise_map = {'Low': 0, 'Medium': 1, 'High': 2}
stress_map = {'Low': 0, 'Medium': 1, 'High': 2}

cause_dict = {
    'CVD Risk': 'Possible causes: High BP, High LDL, Low HDL, Smoking, Obesity, Poor diet, Low physical activity.',
    'Diabetes Risk': 'Possible causes: High BMI, High blood glucose, Family history, Sedentary lifestyle, High sugar intake.',
    'Obesity Risk': 'Possible causes: High BMI, Poor diet, Low activity, Stress, Poor sleep, Family history.',
    'Respiratory Risk': 'Possible causes: Smoking, Air pollution, Chronic cough, Shortness of breath, Family history.',
    'Mental Health Risk': 'Possible causes: High stress, Poor sleep, Anxiety, Mood swings, Family history.'
}

recovery_dict = {
    'CVD Risk': 'How to recover: Quit smoking, Exercise, Balanced diet, Control BP/Cholesterol, Manage stress.',
    'Diabetes Risk': 'How to recover: Weight management, Regular exercise, Balanced diet, Monitor blood sugar, Adequate sleep.',
    'Obesity Risk': 'How to recover: Reduce calorie intake, Increase physical activity, Stress management, Sleep hygiene.',
    'Respiratory Risk': 'How to recover: Quit smoking, Reduce pollution exposure, Breathing exercises, Medical checkup.',
    'Mental Health Risk': 'How to recover: Stress reduction techniques, Mindfulness, Adequate sleep, Social support, Therapy.'
}

@app.route('/')
def landing():
    return render_template('home.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    hashed_pw = generate_password_hash(password)

    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
        conn.commit()
        conn.close()
        return redirect('/?success=1')
    except sqlite3.IntegrityError:
        return "\u274c Username already exists.", 409

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()

    if result and check_password_hash(result[0], password):
        session['user'] = username
        return redirect(url_for('home'))
    else:
        return "\u274c Invalid credentials", 401

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('landing'))

@app.route('/home')
def home():
    if 'user' not in session:
        return redirect(url_for('landing'))
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.form.to_dict()
        features = [
            int(data['Age']),
            gender_map[data['Gender']]
        ] + [
            yes_no_map[data[field]] for field in [
                'Family_History_CVD', 'Family_History_Diabetes', 'Family_History_Obesity',
                'Family_History_Respiratory', 'Family_History_Mental', 'Smoking']
        ] + [
            alcohol_map[data['Alcohol_Consumption']]
        ] + [
            float(data[field]) for field in [
                'BMI', 'Systolic_BP', 'Diastolic_BP', 'Blood_Glucose', 'LDL', 'HDL',
                'Heart_Rate', 'Physical_Activity_Hours_Per_Week', 'Sleep_Hours_Per_Day',
                'Water_Intake_Liters_Per_Day', 'Screen_Time_Hours_Per_Day']
        ] + [
            int(data[field]) for field in [
                'Chest_Pain', 'Shortness_of_Breath', 'Fatigue', 'Chronic_Cough',
                'Mood_Swings', 'Frequent_Urination', 'Increased_Thirst',
                'Sudden_Weight_Change', 'Poor_Concentration', 'Anxiety_Level',
                'Allergy_History', 'Appetite_Changes']
        ] + [
            diet_map[data['Diet_Type']],
            pollution_map[data['Air_Pollution_Exposure']],
            noise_map[data['Noise_Exposure']],
            int(data['Sleep_Quality']),
            stress_map[data['Stress_Level']]
        ]

        input_data = np.array(features).reshape(1, -1)
        prediction = model.predict(input_data)[0]

        risk_names = ['CVD Risk', 'Diabetes Risk', 'Obesity Risk', 'Respiratory Risk', 'Mental Health Risk']
        risks = {risk_names[i]: round(prediction[i], 2) for i in range(5)}
        highest_risk = max(risks, key=risks.get)

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO predict (username, date, input_data, risks, highest_risk)
            VALUES (?, ?, ?, ?, ?)''',
            (session['user'], timestamp, json.dumps(data), json.dumps(risks), highest_risk))
        conn.commit()
        conn.close()

        return render_template('result.html', risks=risks, highest_risk=highest_risk,
                               cause_text=cause_dict[highest_risk],
                               recovery_text=recovery_dict[highest_risk])
    except Exception as e:
        return f"Error: {str(e)}"

basedir = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/save_profile', methods=['POST'])
def save_profile():
    if 'user' not in session:
        return redirect(url_for('landing'))

    username = session['user']
    file = request.files.get('profile_photo')
    filename = None
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{username}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    form = request.form
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS user_profiles (
        username TEXT PRIMARY KEY,
        full_name TEXT, age INTEGER, gender TEXT, email TEXT,
        phone TEXT, address TEXT, city TEXT, state TEXT,
        country TEXT, photo TEXT)''')

    c.execute('''INSERT OR REPLACE INTO user_profiles
        (username, full_name, age, gender, email, phone, address, city, state, country, photo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
        username, form.get('full_name'), form.get('age'), form.get('gender'),
        form.get('email'), form.get('phone'), form.get('address'),
        form.get('city'), form.get('state'), form.get('country'), filename))
    conn.commit()
    conn.close()
    return redirect(url_for('profile'))

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        print(f"Feedback received: {request.form['name']} | {request.form['email']} | {request.form['rating']} | {request.form['message']}")
        return render_template('Feedback.html', success=True)
    return render_template('Feedback.html', success=False)

@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect(url_for('landing'))

    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM user_profiles WHERE username = ?", (session['user'],))
    row = c.fetchone()
    conn.close()
    return render_template('profile.html', profile_data=dict(row) if row else None, show_form=request.args.get('edit') == '1')

@app.route('/history')
def history():
    if 'user' not in session:
        return redirect(url_for('login'))

    try:
        conn = sqlite3.connect('users.db')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM predict WHERE username = ?", (session['user'],))
        rows = cur.fetchall()
        conn.close()

        history_data = [
            {
                'id': row['id'],
                'date': row['date'],
                'input_data': json.loads(row['input_data']),
                'risks': json.loads(row['risks']),
                'highest_risk': row['highest_risk']
            } for row in rows
        ]
        return render_template('history.html', history=history_data)
    except Exception as e:
        return f"An error occurred: {e}", 500

@app.route('/delete-history/<int:id>', methods=['DELETE'])
def delete_history(id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM predict WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True)