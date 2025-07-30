from flask import Flask, render_template, request, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask import url_for
from io import BytesIO
import csv
import os
import requests
import base64
import qrcode


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///people.db'
db = SQLAlchemy(app)
class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    surname = db.Column(db.String(100))
    url = db.Column(db.String(300))

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



                # TODO return URL and store in DB
                for row in data:
                    name = row.get('officialName')
                    surname = row.get('firstName')
                    if name and surname:
                        url="swiyu://?credential_offer=%7B%22credential_issuer%22%3A%22https%3A%2F%2Fcore.trial.procivis-one.com%2Fssi%2Fopenid4vci%2Fdraft-13-swiyu%2F60ee3c1b-e50d-4f6e-8e5b-871106c45674%22%2C%22credential_configuration_ids%22%3A%5B%22https%3A%2F%2Fcore.trial.procivis-one.com%2Fssi%2Fvct%2Fv1%2F700e6b06-472e-4ae9-8385-62566919dbd0%2FHackathon%22%5D%2C%22grants%22%3A%7B%22urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Apre-authorized_code%22%3A%7B%22pre-authorized_code%22%3A%22c75cdc22-4abb-418e-b84e-410fc67c6dd6%22%7D%7D%2C%22credential_subject%22%3A%7B%22keys%22%3A%7B%7D%2C%22wallet_storage_type%22%3A%22SOFTWARE%22%7D%2C%22issuer_did%22%3A%22did%3Atdw%3AQmRhgQMBWT5DUHmjCAC64w86EdBYyoFFQLpRQMdWci2R8U%3Acore.trial.procivis-one.com%3Assi%3Adid-webvh%3Av1%3Ac4f7cafc-ed3a-46d5-a19d-3227c775acd3%22%7D"
                        
                        #add URL in next line
                        person = Person(name=name, surname=surname, url=url)
                        db.session.add(person)

                db.session.commit()

            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                })

    return render_template('index.html')

@app.route('/identification', methods=['GET', 'POST'])
def identification():
    person_exists = None
    name = surname = ""

    if request.method == 'POST':
        name = request.form.get('name')
        surname = request.form.get('surname')

        person = Person.query.filter(
            func.lower(Person.surname) == surname.lower(),
            func.lower(Person.name) == name.lower()
        ).first()

        if person:
            return redirect(url_for('qr_code', person_id=person.id))

        person_exists = False

    return render_template(
        'identification.html',
        name=name,
        surname=surname,
        person_exists=person_exists
    )

@app.route('/people')
def people():
    all_people = Person.query.all()
    return render_template('people.html', people=all_people)

@app.route('/qr/<int:person_id>')
def qr_code(person_id):
    person = Person.query.get_or_404(person_id)
    
    # Generate QR code
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(person.url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Convert image to base64
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return render_template('qr.html', person=person, qr_code_base64=qr_base64)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
    
