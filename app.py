from flask import Flask, request, render_template, redirect, send_from_directory
from werkzeug.utils import secure_filename
import os, json, mysql.connector
from dotenv import load_dotenv
from flask_mail import Mail, Message

load_dotenv()

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ✅ Railway MySQL connection details
DB_CONFIG = {
    'host': 'maglev.proxy.rlwy.net',  # Public Railway host
    'port': 37055,  # Public port
    'user': 'root',
    'password': 'LNNziUlnpqiqEUNrauaTwXhZbgyifYMt',
    'database': 'railway'
}

# Email Config with default fallback
app.config['MAIL_SERVER'] = os.getenv("MAIL_SERVER")
app.config['MAIL_PORT'] = int(os.getenv("MAIL_PORT", 587))
app.config['MAIL_USE_TLS'] = os.getenv("MAIL_USE_TLS", "True") == "True"
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
app.config['MAIL_DEFAULT_SENDER'] = os.getenv("MAIL_DEFAULT_SENDER")

mail = Mail(app)

def get_db_connection():
    """ Function to establish a MySQL DB connection """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

@app.route('/')
def index():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit_form():
    try:
        form_data = request.form.to_dict()
        property_address = secure_filename(form_data.get('property_address', 'unknown'))
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], property_address)
        os.makedirs(folder_path, exist_ok=True)

        uploaded_files = []
        for field_name in ['id_upload', 'proof_income']:
            for file in request.files.getlist(field_name):
                if file.filename:
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(folder_path, filename)
                    file.save(file_path)
                    uploaded_files.append(f"{property_address}/{filename}")

        # Save to DB
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO applications (property_address, form_data, uploaded_files) 
                              VALUES (%s, %s, %s)''', 
                           (property_address, json.dumps(form_data), json.dumps(uploaded_files)))
            conn.commit()
            cursor.close()
            conn.close()
        else:
            print("Failed to connect to the database.")

        # Send Email Notification
        receiver_email = os.getenv("MAIL_RECEIVER")
        if receiver_email:
            msg = Message(f"New Application for {property_address}", recipients=[receiver_email])
            msg.body = f"""
            A new application has been submitted.

            Property Address: {property_address}
            Applicant Info:
            {json.dumps(form_data, indent=2)}

            Uploaded Files:
            {json.dumps(uploaded_files, indent=2)}
            """
            try:
                mail.send(msg)
            except Exception as e:
                print(f"Email sending failed: {e}")
        
        return render_template('success.html', property_address=property_address)

    except Exception as e:
        print(f"Error occurred while processing form submission: {e}")
        return "Internal Server Error", 500

@app.route('/submissions')
def submissions():
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT id, property_address FROM applications')
            apps = cursor.fetchall()
            cursor.close()
            conn.close()
            return render_template('submissions.html', applications=apps)
        else:
            return "Database connection failed", 500
    except Exception as e:
        print(f"Error fetching submissions: {e}")
        return "Internal Server Error", 500

@app.route('/submission/<int:app_id>')
def submission_detail(app_id):
    try:
        conn = get_db_connection()
        if conn:
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
        else:
            return "Database connection failed", 500
    except Exception as e:
        print(f"Error fetching submission details: {e}")
        return "Internal Server Error", 500

@app.route('/uploads/<property>/<filename>')
def uploaded_file(property, filename):
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], property)
    return send_from_directory(folder_path, filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
