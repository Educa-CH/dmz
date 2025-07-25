from flask import Flask, render_template, request, redirect, jsonify
import csv
import os
import requests

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Stelle sicher, dass der Upload-Ordner existiert
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def parse_flat_csv(filepath):
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        data = []
        for row in reader:
            flat_row = {}
            for key, value in row.items():
                # Sicherheitsprüfung: key und value müssen existieren
                if key is None:
                    continue  # ignoriere fehlerhafte Spalten

                # value vorbereiten
                if value is None:
                    value = ""
                elif not isinstance(value, str):
                    value = str(value)

                value = value.strip()

                # leere Strings → None
                if value == "":
                    flat_row[key] = None
                elif key == "thesis_grade" or key.startswith("grade_"):
                    try:
                        flat_row[key] = int(value)
                    except ValueError:
                        flat_row[key] = value
                else:
                    flat_row[key] = value
            data.append(flat_row)
        return data



@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Datei aus dem Formular
        file = request.files['file']
        if file and file.filename.endswith('.csv'):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)

            data = parse_flat_csv(filepath)

            # API Call (Platzhalter-URL)
            api_url = 'https://api.example.com/endpoint'  # ← später ersetzen
            try:
                
                print(data)

                #response = requests.post(api_url, json=data)
                #return jsonify({
                #    'status': 'success',
                #    'api_response': response.json()
                #})
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                })

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
