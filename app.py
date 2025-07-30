import json
from flask import Flask, render_template, request, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask import url_for
from io import BytesIO
import csv
import os
import requests
import http.client
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

            try:
                
                # printing .csv data
                print(data)


                # Step 1: Retrieving all the credential schemas
                # In a real world scenario you would filter the schema you need by name
                accessToken = 'eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJXcGtGQ3Zhbjltbk13U29lTmdITHlKdDBGZmZpRmlEY1J2eFJvdFFNWFFnIn0.eyJleHAiOjE3NTM5MDU3NzEsImlhdCI6MTc1Mzg2MjU3MSwianRpIjoidHJydGNjOmExMzVlZGNhLTU5NDEtNDA2MC05NGU0LTJhMDdmZTNhODViNyIsImlzcyI6Imh0dHBzOi8va2V5Y2xvYWsudHJpYWwucHJvY2l2aXMtb25lLmNvbS9yZWFsbXMvdHJpYWwiLCJhdWQiOlsib25lLWJmZi1jbGllbnQiLCJhY2NvdW50Il0sInN1YiI6IjI2YmZjZDBiLTRlNWQtNDQ5YS1hNWQ3LWMzYWVkZDljNWE3NSIsInR5cCI6IkJlYXJlciIsImF6cCI6Im9uZS1lZHVjYSIsImFjciI6IjEiLCJhbGxvd2VkLW9yaWdpbnMiOlsiLyoiXSwicmVhbG1fYWNjZXNzIjp7InJvbGVzIjpbIm9mZmxpbmVfYWNjZXNzIiwiRWR1Y2FfRURJVE9SIiwidW1hX2F1dGhvcml6YXRpb24iLCJkZWZhdWx0LXJvbGVzLXRyaWFsIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19fSwic2NvcGUiOiJncm91cCBwcm9maWxlIGVtYWlsIiwiZW1haWxfdmVyaWZpZWQiOmZhbHNlLCJjbGllbnRIb3N0IjoiMTAuMS4yLjEiLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJzZXJ2aWNlLWFjY291bnQtb25lLWVkdWNhIiwiY2xpZW50QWRkcmVzcyI6IjEwLjEuMi4xIiwiY2xpZW50X2lkIjoib25lLWVkdWNhIn0.ZNyu3CqlkKGB1v40PPRJiAlenrlVuAcWeAeu7NeF7PxSBIUt2DY2qegTly1IWq5_XL3U_j3b6mKa-Th1BOtMQ5k4KzLx_ffJ3LAMHiQDRfjD6Pemdh6b9O93MKPQ26Jo1noOy5cI0F7DXcHRR0EptOhYneGYDNaoE9yVsS9FO3yT1UGqtkzrashos1H-rjrSzLUK1IM8xpFPX-9fAn294azaWk66nhF7xLlvIqlvYK_yhreBmHgrvVcrYEEWnvAMZ4e001RVeDAZd92dm4STNAPM0peFzR0-2QRdKW_l_MWD5bqvL1q3RB5n-VZo8yDp1aGBrTc8aRmgZtG45V7yaA'
                connection = http.client.HTTPSConnection(host='api.trial.procivis-one.com')
                
                baseHeaders = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {accessToken}' 
                }
                connection.request("GET", "/api/credential-schema/v1", '', baseHeaders)
                schemeListResponse = connection.getresponse()

                # Getting all the schemas
                schemeList = schemeListResponse.read().decode('utf-8')
                #print(json.dumps(schemeListString, indent=2))

                #TODO: Selecting the schema you want from the scheme list

                # Step 2
                # Retrieving the schema we need

                #hardcoded in this example, from the json above
                schemaNeeded = '66b0d9ea-6326-4539-85f0-c177a7820abe'
                schemaEndpoint = f"/api/credential-schema/v1/{schemaNeeded}"
                connection.request("GET", schemaEndpoint, '', baseHeaders)
                chosenSchemaResponse = connection.getresponse()
                chosenSchema = chosenSchemaResponse.read().decode('utf-8')
                #print(json.dumps(correctSchemeString, indent=2))

                # Step 3
                # Retrieve the right identifier to be used as issue > https://docs.procivis.ch/reference/desk/list-identifiers
                connection.request("GET", '/api/identifier/v1', '', baseHeaders)
                allIdentifiersResponse = connection.getresponse()
                allIdentifiers = allIdentifiersResponse.read().decode('utf-8')

                # Step 4
                # Ceate the credential by using the ID of the claim in the schema
                # it will return the credential ID
                #TODO: Using the right schema ID, obtained in step 2
                #TODO: Using the right issuer ID, obtained in step 3
                credentialPayload = json.dumps({
                "credentialSchemaId": "66b0d9ea-6326-4539-85f0-c177a7820abe",
                "issuer": "f2164b6f-db9c-4807-94a8-9aad37c0bd4b",
                "protocol": "OPENID4VCI_DRAFT13_SWIYU",
                "claimValues": [
                    {
                    "claimId": "6b683bf6-1fa6-42fe-8ea5-30e2527eb0af",
                    "path": "Field",
                    "value": "Davide",
                    }
                ]
                })
                credentialHeaders = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': f'Bearer {accessToken}' 
                }
                connection.request("POST", "/api/credential/v1", credentialPayload, credentialHeaders)
                credentialCreatedResponse = connection.getresponse()
                credentialCreated = credentialCreatedResponse.read().decode("utf-8")

                # Step 5
                # Issuing the credential
                #TODO: using the ID of the credential created in step 4
                #hardcoded at the moment - HackatonTest schema
                credentialId = '2714aa43-4b54-4cde-b064-4d0e4a7424b3'
                issuingCredentialEndpoint = f"/api/credential/v1/{credentialId}/share"
                connection.request("POST", issuingCredentialEndpoint, '', baseHeaders)
                credentialIssuedResponse = connection.getresponse()
                credentialIssued = credentialIssuedResponse.read().decode("utf-8")
                


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