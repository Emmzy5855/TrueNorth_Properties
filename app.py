from flask import Flask, request, render_template, redirect, send_from_directory
from werkzeug.utils import secure_filename
import os, json, mysql.connector
from dotenv import load_dotenv

load_dotenv()  # Load from .env

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DB_CONFIG = {
    'host': 'maglev.proxy.rlwy.net',
    'port': 55641,
    'user': 'root',
    'password': 'WWWohlVZHMSYgmmikzqgTWGXMUEpttYH',
    'database': 'railway'
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

@app.route('/')
def index():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit_form():
    form_data = request.form.to_dict()
    property_address = secure_filename(form_data.get('property_address', 'unknown').replace(" ", "_"))
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], property_address)
    os.makedirs(folder_path, exist_ok=True)

    uploaded_files = []
    for field_name in ['id_upload[]', 'proof_income[]']:
        for file in request.files.getlist(field_name):
            if file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(folder_path, filename)
                file.save(file_path)
                uploaded_files.append(file_path)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO applications (property_address, form_data, uploaded_files)
        VALUES (%s, %s, %s)
    ''', (property_address, json.dumps(form_data), json.dumps(uploaded_files)))
    conn.commit()
    cursor.close()
    conn.close()

    return render_template('success.html', property_address=property_address)

@app.route('/submissions')
def submissions():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT id, property_address FROM applications')
    apps = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('submissions.html', applications=apps)

@app.route('/submission/<int:app_id>')
def submission_detail(app_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM applications WHERE id = %s', (app_id,))
    app_data = cursor.fetchone()
    cursor.close()
    conn.close()
    if not app_data:
        return "Not found", 404
    return render_template('submission_detail.html',
                           form_data=json.loads(app_data['form_data']),
                           files=json.loads(app_data['uploaded_files']))

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
