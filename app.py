import os
import json
import sqlite3
from flask import Flask, request, render_template, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'submissions'
DATABASE = 'applications.db'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize SQLite DB
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_address TEXT,
                form_data TEXT,
                files TEXT
            )
        ''')
        conn.commit()

init_db()

# Home page: Form
@app.route('/')
def index():
    try:
        return render_template('form.html')
    except Exception as e:
        return f"Error: {e}"

# Submit form
@app.route('/submit', methods=['POST'])
def submit_form():
    form_data = request.form.to_dict()
    property_address = secure_filename(form_data.get('property_address', 'no_address').replace(" ", "_"))
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], property_address)
    os.makedirs(folder_path, exist_ok=True)

    uploaded_files = []

    # Handle file uploads
    for field_name in ['id_upload[]', 'proof_income[]']:
        files = request.files.getlist(field_name)
        for file in files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(folder_path, filename)
                file.save(file_path)
                uploaded_files.append(filename)

    # Save to database
    with sqlite3.connect(DATABASE) as conn:
        conn.execute(
            "INSERT INTO applications (property_address, form_data, files) VALUES (?, ?, ?)",
            (property_address, json.dumps(form_data), json.dumps(uploaded_files))
        )
        conn.commit()

    return render_template('success.html', property_address=property_address)

# View submitted applications
@app.route('/applications')
def view_applications():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, property_address, form_data, files FROM applications")
        entries = cursor.fetchall()

    html = "<h2>Submitted Applications</h2><table border='1'><tr><th>Property</th><th>Form Data</th><th>Files</th></tr>"
    for entry in entries:
        form_data = json.loads(entry[2])
        files = json.loads(entry[3])
        file_links = " | ".join(
            f"<a href='/uploads/{entry[1]}/{f}'>{f}</a>" for f in files
        )
        html += f"<tr><td>{entry[1]}</td><td><pre>{json.dumps(form_data, indent=2)}</pre></td><td>{file_links}</td></tr>"
    html += "</table>"

    return html

# Serve uploaded files
@app.route('/uploads/<property>/<filename>')
def uploaded_file(property, filename):
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], property), filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
