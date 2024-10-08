from flask import Flask, flash, redirect, render_template, request, session, jsonify, send_from_directory
from flask_session import Session
import os
import subprocess
from datetime import datetime
import papermill as pm

PREDICTIONS_FOLDER = '/workspaces/173840073/project/website/prediction'

# Configure application
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management
app.config['UPLOAD_FOLDER'] = '/workspaces/173840073/project/website/uploads'  # Replace with your upload folder path

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'csvFile' not in request.files:
        return "No file part"

    file = request.files['csvFile']

    if file.filename == '':
        return "No selected file"

    if file:
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        session['file_path'] = file_path  # Save the file path in the session
        return redirect('/process')

@app.route('/process', methods=['GET'])
def process():
    # Retrieve the file path from the session
    file_path = session.get('file_path')
    if not file_path:
        return "No file uploaded in this session"

    # Use the file path and additional parameters in your machine learning model
    result = run_notebook(file_path)

    # Find the most recent prediction file
    files = [os.path.join(PREDICTIONS_FOLDER, f) for f in os.listdir(PREDICTIONS_FOLDER) if os.path.isfile(os.path.join(PREDICTIONS_FOLDER, f))]
    if not files:
        return "No prediction files found."

    latest_file = max(files, key=os.path.getctime)
    prediction_file_path = os.path.relpath(latest_file, start=PREDICTIONS_FOLDER)

    return render_template('result.html', prediction_file_path=prediction_file_path)

def run_notebook(file_path):
    try:
        # Paths to the input and output notebooks
        input_notebook = 'Machine.ipynb'
        output_notebook = 'output/output_notebook.ipynb'

        # Run the notebook with papermill
        pm.execute_notebook(
            input_path=input_notebook,
            output_path=output_notebook,
            parameters=dict(file_path=file_path)
        )

        return "Notebook executed successfully"
    except Exception as e:
        return str(e)

@app.route('/api/predictions', methods=['GET']) # Used github copilot
def list_predictions():
    files = []
    for filename in os.listdir(PREDICTIONS_FOLDER):
        filepath = os.path.join(PREDICTIONS_FOLDER, filename)
        if os.path.isfile(filepath):
            creation_time = os.path.getctime(filepath)
            files.append({
                'name': filename,
                'creationTime': datetime.fromtimestamp(creation_time).isoformat()
            })
    return jsonify(files)

@app.route('/predictions/<filename>', methods=['GET']) # used github co pilot to save the predicted file in the prediction folder
def download_prediction(filename):
    return send_from_directory(PREDICTIONS_FOLDER, filename)



if __name__ == '__main__':
    app.run(debug=True)

if __name__ == '__main__':
    app.run(debug=True)
