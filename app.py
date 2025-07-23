from flask import Flask, request, render_template, redirect, url_for
import os
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'submissions'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    try:
        return render_template('form.html')
    except Exception as e:
        return f"Error: {e}"


@app.route('/submit', methods=['POST'])
def submit_form():
    # Get form data
    form_data = request.form.to_dict()

    # Clean and create folder from property_address
    property_address = secure_filename(form_data['property_address'].replace(" ", "_"))
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], property_address)
    os.makedirs(folder_path, exist_ok=True)

    # Save form data as JSON
    with open(os.path.join(folder_path, 'application.json'), 'w') as f:
        json.dump(form_data, f, indent=2)

    # Save uploaded files
    for field_name in ['id_upload[]', 'proof_income[]']:
        files = request.files.getlist(field_name)
        for file in files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(folder_path, filename))

    return render_template('success.html', property_address=property_address)

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
