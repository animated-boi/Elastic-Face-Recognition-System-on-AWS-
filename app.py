import csv
from flask import Flask, request

app = Flask(__name__)

# Load the CSV into a dictionary
lookup_table = {}
with open('classification_face_images_1000.csv', mode='r') as infile:
    reader = csv.reader(infile)
    next(reader)  # Skip header row
    lookup_table = {rows[0]: rows[1] for rows in reader}

@app.route("/", methods=["POST"])
def upload_file():
    if 'inputFile' not in request.files:
        return "No file part", 400
    file = request.files['inputFile']
    if file.filename == '':
        return "No selected file", 400

    # Debug: Print the uploaded filename
    filename = file.filename
    print(f"Uploaded filename: {filename}")

    # Lookup the filename in the CSV lookup table
    # We need to ensure the filename matches the format in the CSV
    result = lookup_table.get(filename.split('.')[0], "Unknown")

    return f"{filename}:{result}"
