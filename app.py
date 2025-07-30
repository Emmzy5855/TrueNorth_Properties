from flask import Flask, request, render_template, redirect, url_for
import os
import json
import sqlite3
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = 'mysql://root:WWWohlVZHMSYgmmikzqgTWGXMUEpttYH@maglev.proxy.rlwy.net/railway'
DATABASE = 'applications.db'

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Database Setup ---
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_address TEXT NOT NULL,
            form_data TEXT NOT NULL,
            uploaded_files TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Initialize database
init_db()

@app.route('/')
def index():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit_form():
    form_data = request.form.to_dict()
    property_address = secure_filename(form_data.get('property_address', 'unknown').replace(" ", "_"))

    # Create folder for uploads
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], property_address)
    os.makedirs(folder_path, exist_ok=True)

    # Save uploaded files
    uploaded_files = []
    for field_name in ['id_upload[]', 'proof_income[]']:
        files = request.files.getlist(field_name)
        for file in files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(folder_path, filename)
                file.save(file_path)
                uploaded_files.append(file_path)

    # Save data in database
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO applications (property_address, form_data, uploaded_files)
        VALUES (?, ?, ?)
    ''', (property_address, json.dumps(form_data), json.dumps(uploaded_files)))
    conn.commit()
    conn.close()

    return render_template('success.html', property_address=property_address)

@app.route('/submissions')
def submissions():
    conn = get_db_connection()
    apps = conn.execute('SELECT id, property_address FROM applications').fetchall()
    conn.close()
    return render_template('submissions.html', applications=apps)

@app.route('/submission/<int:app_id>')
def submission_detail(app_id):
    conn = get_db_connection()
    app_data = conn.execute('SELECT * FROM applications WHERE id = ?', (app_id,)).fetchone()
    conn.close()

    if not app_data:
        return "Application not found.", 404

    form_data = json.loads(app_data['form_data'])
    uploaded_files = json.loads(app_data['uploaded_files']) if app_data['uploaded_files'] else []

    return render_template('submission_detail.html', form_data=form_data, files=uploaded_files)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
