from flask import Flask, request, render_template, redirect, url_for, send_from_directory
import os
import json
import mysql.connector
from werkzeug.utils import secure_filename

app = Flask(__name__)

# --- Configuration ---
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# MySQL connection settings
DB_CONFIG = {
    'host': 'maglev.proxy.rlwy.net',
    'port': 55641,
    'user': 'root',
    'password': 'WWWohlVZHMSYgmmikzqgTWGXMUEpttYH',
    'database': 'railway'
}

# Ensure the uploads folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- Helper Function: MySQL Connection ---
def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# --- Routes ---

@app.route('/')
def index():
    return render_template('form.html')


@app.route('/submit', methods=['POST'])
def submit_form():
    form_data = request.form.to_dict()
    property_address = secure_filename(form_data.get('property_address', 'unknown').replace(" ", "_"))

    # Make folder path for this submission
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], property_address)
    os.makedirs(folder_path, exist_ok=True)

    uploaded_files = []

    for field in ['id_upload[]', 'proof_income[]']:
        for file in request.files.getlist(field):
            if file and file.filename:
                filename = secure_filename(file.filename)
                save_path = os.path.join(folder_path, filename)
                file.save(save_path)
                uploaded_files.append(os.path.join(property_address, filename))  # Store relative path

    # Save to DB
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO applications (property_address, form_data, uploaded_files)
        VALUES (%s, %s, %s)
    ''', (
        property_address,
        json.dumps(form_data),
        json.dumps(uploaded_files)
    ))
    conn.commit()
    cursor.close()
    conn.close()

    return render_template('success.html', property_address=property_address)


@app.route('/submissions')
def submissions():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT id, property_address FROM applications')
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('submissions.html', applications=rows)


@app.route('/submission/<int:app_id>')
def submission_detail(app_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM applications WHERE id = %s', (app_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        return "Application not found.", 404

    form_data = json.loads(row['form_data'])
    uploaded_files = json.loads(row['uploaded_files']) if row['uploaded_files'] else []

    return render_template('submission_detail.html', form_data=form_data, files=uploaded_files)


# 🔥 Serve files from the uploads/ folder
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --- Run ---
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
