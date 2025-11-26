from flask import Flask, render_template, request, redirect, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_babel import Babel, _
from sqlalchemy import func, Text
from flask import url_for
from io import BytesIO
from io import StringIO
from werkzeug.exceptions import BadRequest
from datetime import date, timedelta, datetime
import csv
import os
import requests
import http.client
import base64
import qrcode
import json
import time
import io
import random


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = 'supersupersecretkey'
app.config['BABEL_DEFAULT_LOCALE'] = 'de'  # default language
app.config['BABEL_SUPPORTED_LOCALES'] = ['de', 'fr']


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///people.db'
db = SQLAlchemy(app)
class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    surname = db.Column(db.String(100))
    dateOfBirth = db.Column(db.String(10))
    url = db.Column(db.String(300))


class Registered(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    surname = db.Column(db.String(100))
    dateOfBirth = db.Column(db.String(10))
    program = db.Column(db.String(300))
    validation = db.Column(db.Boolean)
    registration_method = db.Column(db.String)
    portrait = db.Column(Text)    

with app.app_context():
    db.create_all()    

# Store key in memory (works if you have one app process; use Redis for multi-process)
api_key_cache = {
    "key": None,
    "expires_at": 0
}    

# Stelle sicher, dass der Upload-Ordner existiert
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_locale():
    # 1. Check query parameter first
    lang = request.args.get('lang')
    if lang:
        session['lang'] = lang  # save in session
    # 2. Check session
    return session.get('lang', app.config['BABEL_DEFAULT_LOCALE'])

babel = Babel(app, locale_selector=get_locale)

# check the structure of newly uploaded csv
def csv_check(csv_string):
    # Path to the reference CSV
    reference_path = os.path.join("uploads", "sample.dmz.csv")
    
    # Read header from reference CSV
    with open(reference_path, "r", newline='', encoding="utf-8") as ref_file:
        ref_reader = csv.reader(ref_file)
        ref_header = next(ref_reader, [])
    
    # Read header from given CSV string
    input_reader = csv.reader(io.StringIO(csv_string))
    input_header = next(input_reader, [])
    
    # Compare: same set of fields & same count
    return (
        len(ref_header) == len(input_header) and
        set(ref_header) == set(input_header)
    )

def csv_to_json(csv_string):
    f = StringIO(csv_string)
    reader = csv.DictReader(f)
    data = [row for row in reader]
    return data  # return Python list of dicts (JSON object)

def get_api_key():
    now = time.time()

    # Only refresh if expired or not set
    if not api_key_cache["key"] or now >= api_key_cache["expires_at"]:
        print("Refreshing API key...")
        resp = requests.post(
            "https://keycloak.trial.procivis-one.com/realms/trial/protocol/openid-connect/token",
            data={
                "client_id": "one-educa",
                "client_secret": "Y1oOzalI4idJoN9pIdrYpMFuSL0UB8hh",
                "grant_type": "client_credentials",
                "scope":"openid"
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
        data = resp.json()
        api_key_cache["key"] = data["access_token"]
        api_key_cache["expires_at"] = now + data["expires_in"] - 60  # refresh 1 min early

    return api_key_cache["key"]

def to_isoformat(value):
    """
    Convert any input to a date string 'YYYY-MM-DD' for DB comparison.
    """
    if value is None:
        return None

    if isinstance(value, date):
        return value.isoformat()  # date.isoformat() -> 'YYYY-MM-DD'

    if isinstance(value, datetime):
        return value.date().isoformat()  # drop time

    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value).date().isoformat()

    if isinstance(value, str):
        # Try ISO format first
        try:
            dt = datetime.fromisoformat(value)
            return dt.date().isoformat()
        except ValueError:
            pass
        
        # Common string formats
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%Y/%m/%d", "%d.%m.%Y"):
            try:
                dt = datetime.strptime(value, fmt)
                return dt.date().isoformat()
            except ValueError:
                continue
        
        raise ValueError(f"Unrecognized date format: {value}")

    raise TypeError(f"Cannot convert type {type(value)} to DB date string")

@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in app.config['BABEL_SUPPORTED_LOCALES']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('index'))  

@app.route('/overview')
def overview():
    return render_template('overview.html')  

@app.route('/admin')
def admin():
    return render_template('admin.html')   

@app.route('/', methods=['GET', 'POST'])
def upload_file():

    accessToken = get_api_key()

    if request.method == 'POST':
        # Datei aus dem Formular
        file = request.files['file']
        if file and file.filename.endswith('.csv'):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)

            file.stream.seek(0)
            csv_string = file.read().decode('utf-8')

            try:    
                if not csv_check(csv_string):
                    # this should ideally be something more intelligent             
                    pass        
                    
                data = csv_to_json(csv_string)
             
                # printing .csv data
                print(data)

                # Step 1: Retrieving all the credential schemas
                # In a real world scenario you would filter the schema you need by name
                connection = http.client.HTTPSConnection(host='api.trial.procivis-one.com')
                
                baseHeaders = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {accessToken}' 
                }
                #connection.request("GET", "/api/credential-schema/v1", '', baseHeaders)
                #schemeListResponse = connection.getresponse()

                # Getting all the schemas
                #schemeList = schemeListResponse.read().decode('utf-8')
                #print(json.dumps(schemeListString, indent=2))

                #TODO: Selecting the schema you want from the scheme list

                # Step 2
                # Retrieving the schema we need

                #hardcoded in this example, from the json above
                #schemaNeeded = '9841791e-06a4-4805-bfc9-d3286b851fdf'
                #schemaEndpoint = f"/api/credential-schema/v1/{schemaNeeded}"
                #connection.request("GET", schemaEndpoint, '', baseHeaders)
                #chosenSchemaResponse = connection.getresponse()
                #chosenSchema = chosenSchemaResponse.read().decode('utf-8')
                #print(json.dumps(correctSchemeString, indent=2))

                # Step 3
                # Retrieve the right identifier to be used as issue > https://docs.procivis.ch/reference/desk/list-identifiers
                #connection.request("GET", '/api/identifier/v1', '', baseHeaders)
                #allIdentifiersResponse = connection.getresponse()
                #allIdentifiers = allIdentifiersResponse.read().decode('utf-8')

                # Step 4
                # Ceate the credential by using the ID of the claim in the schema
                # it will return the credential ID
                #TODO: Using the right schema ID, obtained in step 2
                #TODO: Using the right issuer ID, obtained in step 3
                credentialPayload = json.dumps({
                "credentialSchemaId": "9841791e-06a4-4805-bfc9-d3286b851fdf",
                "issuer": "f2164b6f-db9c-4807-94a8-9aad37c0bd4b",
                "protocol": "OPENID4VCI_DRAFT13_SWIYU",
                "claimValues": [
                    {
                    "claimId": "6fd5458f-bce7-46b8-bc6a-f7cfa9ac7d31",
                    "path": "Vorname",
                    "value": data[0]["firstName"],
                    },
                    {
                    "claimId": "d0660762-8940-4f81-9901-3d231be717da",
                    "path": "Nachname",
                    "value": data[0]["officialName"],
                    },
                    {
                    "claimId": "24a77a50-8b15-415e-abf0-3d3186b897a1",
                    "path": "Heimatort",
                    "value": data[0]["originName"],
                    },
                    {
                    "claimId": "cf2442bb-72e0-41dc-b6fd-20a336293034",
                    "path": "Geburtsdatum",
                    "value": data[0]["dateOfBirth"],
                    },
                    {
                    "claimId": "2f9a6cae-7ccb-4b8b-aac4-ad56d061115a",
                    "path": "Ausbildung von:",
                    "value": data[0]["durationFrom"],
                    },
                    {
                    "claimId": "33f6452e-f415-46bb-8964-7c103e16da4c",
                    "path": "Ausbildung bis:",
                    "value": data[0]["durationTo"],
                    },
                    {
                    "claimId": "0702996f-c90e-4dc6-a4e4-ca8e8811ba0d",
                    "path": "Französisch",
                    "value": data[0]["french"],
                    },
                    {
                    "claimId": "a801d3d2-4ed1-437e-8b3e-7f3243d082ba",
                    "path": "Deutsch",
                    "value": data[0]["german"],
                    },
                    {
                    "claimId": "65627ef3-5101-4b02-b78f-69eda89ca589",
                    "path": "Englisch",
                    "value": data[0]["english"],
                    },
                    {
                    "claimId": "af486e01-8dd6-4680-9200-fe7e7ae41a89",
                    "path": "Mathematik",
                    "value": data[0]["math"],
                    },
                    {
                    "claimId": "25ba9a2c-bd94-4697-9a7d-8d58920329fd",
                    "path": "Mathematik Stufe",
                    "value": data[0]["level_math"],
                    },
                    {
                    "claimId": "ed307a4b-de9b-4b04-a484-7bc2e21e1839",
                    "path": "Biologie",
                    "value": data[0]["biology"],
                    },
                    {
                    "claimId": "b4d355aa-1818-4f41-aa43-c26955bd4f02",
                    "path": "Chemie",
                    "value": data[0]["chemistry"],
                    },
                    {
                    "claimId": "07d9ee66-8d58-48cb-aef5-a96c88497365",
                    "path": "Physik",
                    "value": data[0]["physics"],
                    },
                    {
                    "claimId": "91a67c63-4d6c-410b-90e2-c81a4101cfd7",
                    "path": "Geschichte",
                    "value": data[0]["history"],
                    },
                    {
                    "claimId": "b2351983-f713-45e7-82d2-cd09b3ac6fce",
                    "path": "Philosophie",
                    "value": data[0]["philosophy"],
                    },
                    {
                    "claimId": "58864289-d777-483d-82ba-c0c5039cef27",
                    "path": "Bildende Künste",
                    "value": data[0]["visual_arts"],
                    },
                    {
                    "claimId": "c5dc97fd-b60c-4348-85c8-1a0b828c4d95",
                    "path": "Wahlfach Name",
                    "value": data[0]["elective_name"],
                    },
                    {
                    "claimId": "8bb4250f-02bf-4576-bfa6-ed887b67c740",
                    "path": "Wahlfach Note",
                    "value": data[0]["elective_grade"],
                    },
                    {
                    "claimId": "b320a13a-1f6e-4980-84c6-2df817315f6c",
                    "path": "Ergänzungsfach Name",
                    "value": data[0]["supplementary_subject"],
                    },
                    {
                    "claimId": "1e745fa6-f7ef-4a79-a7b1-64069cc07fc5",
                    "path": "Ergänzungsfach Note",
                    "value": data[0]["supplementary_subject_grade"],
                    },
                    {
                    "claimId": "17e30929-e1bc-454d-a9f5-cc4b5d5d7da6",
                    "path": "Maturaarbeit",
                    "value": data[0]["thesis_title"],
                    },
                    {
                    "claimId": "8ec4771f-e9af-4676-8c04-32e368093f7d",
                    "path": "Maturaarbeit Note",
                    "value": data[0]["thesis_grade"],
                    },
                    {
                    "claimId": "42d7f826-1f03-4e19-a573-958bd4ffb735",
                    "path": "Kantonsname",
                    "value": data[0]["canton"],
                    },
                    {
                    "claimId": "6a8e2530-30d8-4989-b285-4b83fb7e3cd5",
                    "path": "Schulname",
                    "value": data[0]["school_name"],
                    },
                    {
                    "claimId": "7000200b-07ac-47e9-8cbd-66a6495d8017",
                    "path": "Schulort",
                    "value": data[0]["municipalityName"],
                    },
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

                print(credentialCreated)    

                credentialId = json.loads(credentialCreated)['id']

                
                print(credentialId)

                # Step 5
                # Issuing the credential
                #TODO: using the ID of the credential created in step 4
                #hardcoded at the moment - HackatonTest schema
                issuingCredentialEndpoint = f"/api/credential/v1/{credentialId}/share"
                connection.request("POST", issuingCredentialEndpoint, '', baseHeaders)
                credentialIssuedResponse = connection.getresponse()
                credentialIssued = credentialIssuedResponse.read().decode("utf-8")

                print(credentialIssued)
                
                url = json.loads(credentialIssued)['url']

                for row in data:
                    name = row.get('officialName')
                    surname = row.get('firstName')
                    dateOfBirth = row.get('dateOfBirth')

                    if name and surname and dateOfBirth:
                        # Check if this person already exists in DB
                        existing_person = Person.query.filter_by(
                            name=name,
                            surname=surname,
                            dateOfBirth=dateOfBirth
                        ).first()

                        if existing_person:
                            # Update existing record
                            existing_person.url = url
                        else:
                            # Create a new record
                            new_person = Person(
                                name=name,
                                surname=surname,
                                dateOfBirth=dateOfBirth,
                                url=url
                            )
                            db.session.add(new_person)

                db.session.commit()

                return render_template('success.html', prompt="Digitales Maturazeugnis für " + name + " " + surname + " erfolgreich erstellt!")

            except Exception as e:
                print(e)
                return render_template('failure.html',message=e)

    return render_template('index.html')

@app.route('/identification', methods=['GET', 'POST'])
def identification():
    person_exists = None
    name = surname = ""

    if request.method == 'POST':
        name = request.form.get('name')
        surname = request.form.get('surname')
        dateOfBirth = request.form.get('dateOfBirth')

        print("Name: " + name + " Surname: " + surname )

        person = Person.query.filter(
            func.lower(Person.surname) == surname.lower(),
            func.lower(Person.name) == name.lower(),
            Person.dateOfBirth == dateOfBirth
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

@app.route('/registered')
def registered():
    all_registered = Registered.query.all()
    return render_template('registered.html', registered=all_registered)

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

    # Delete person after QR is generated, as QR Code is only valid once for scanning
    db.session.delete(person)
    db.session.commit()

    return render_template('qr.html', person=person, qr_code_base64=qr_base64)


@app.route('/university', methods=['GET', 'POST'])
def select_program():
    

    if request.method == 'POST':
        session['program'] = request.form.get('program')
        return render_template('register.html',program=session['program']) 
        
    return render_template('university.html')

@app.route('/register', methods=['GET', 'POST'])
def register_method():
    method = request.form.get('method')
    if method == 'e-id':
        return render_template('register-e-id.html')
    elif method == 'maturazeugnis':
        return render_template('register-mz.html', program=session['program'])
    return render_template('register.html',program=session['program'])

    
@app.route('/register-mz', methods=['GET', 'POST'])
def register_mz():
    if request.method == 'POST':
        name = request.form.get('name') 
        surname = request.form.get('surname')
        dateOfBirth = request.form.get('dateOfBirth')
        portrait = request.files['file']
        validation = False
        program = session['program']
        registration_method = 'Manual'

        try:
            print(datetime.strptime(dateOfBirth, "%Y-%m-%d"))
            datetime.strptime(dateOfBirth, "%Y-%m-%d")
        except ValueError:
            return render_template('register-mz.html', error=_("Datum muss folgendes Format haben YYYY-MM-DD"))

        max_size_bytes = 4 * 1024 * 1024 # 4MiB
        file_bytes = portrait.read()
        if len(file_bytes) > max_size_bytes:
            return render_template('register-mz.html', program=session['program'], file_valid=False)

    
        file_str = base64.b64encode(file_bytes).decode('utf-8')
        file_str = f"data:image/jpeg;base64,{file_str}"

        print(file_str)
        # Create a new record
        new_registered = Registered(
            name=name,
            surname=surname,
            dateOfBirth=dateOfBirth,
            program=program,
            validation=validation,
            portrait=file_str,
            registration_method=registration_method
        )
        db.session.add(new_registered)
        db.session.commit() 
    
        return redirect(url_for('validation'))
    return render_template('register-mz.html', program=session['program'])


@app.route('/register-e-id')
def register_e_id():
    #Step 1 > config
    accessToken = get_api_key()
    conn = http.client.HTTPSConnection(host='api.trial.procivis-one.com')
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json', 
        'Authorization': f'Bearer {accessToken}'
    }
    # Step 4 > Creating the proof request
    proofPayload = json.dumps({
        "proofSchemaId": "c0644df6-db7f-4e72-a1f4-ea4a30d81873", #official swyiu beta id
        "verifier": "b92bf54c-e91e-4537-94d6-bf804649bf0a",
        "protocol": "OPENID4VP_DRAFT20_SWIYU"
    })

    conn.request("POST", "/api/proof-request/v1", proofPayload, headers)
    proofCreatedResponse = conn.getresponse()
    proofCreatedId = json.loads(proofCreatedResponse.read().decode("utf-8"))["id"]

    # Step 5 > Requesting proof for the proofCreatedId
    conn.request("POST", f"/api/proof-request/v1/{proofCreatedId}/share", '', headers)
    individualProofRequestResponse = conn.getresponse()
    share_url = json.loads(individualProofRequestResponse.read().decode()).get("url")
    print(share_url)

    # Step 6 > Generate QR code
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(share_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return render_template('register-e-id.html', qr_code_base64=qr_base64, proof_id=proofCreatedId)

@app.route('/register-e-id/status/<proof_id>')
def eid_proof_status(proof_id):
    print("Status request..." + proof_id)
    accessToken = get_api_key()
    connection = http.client.HTTPSConnection(host='api.trial.procivis-one.com')
    
    baseHeaders = {
        'Accept': 'application/json',
        'Content-Type': 'application/json', 
        'Authorization': f'Bearer {accessToken}' 
    }

    proofRequestsEndpoint = f"/api/proof-request/v1/{proof_id}"
    connection.request("GET", proofRequestsEndpoint, '', baseHeaders)
    proofRequestsResponse = connection.getresponse()
    proofRequests = proofRequestsResponse.read().decode("utf-8")

    state = json.loads(proofRequests)['state']
    
    if state == "ACCEPTED":
        data = json.loads(proofRequests)
        # Get the first proof input
        proof_input = data['proofInputs'][0]
        # Create a dictionary of key-value pairs
        claims_dict = {claim['schema']['key']: claim['value'] for claim in proof_input['claims']}

        print(claims_dict['given_name'])

        name = claims_dict['family_name']
        surname = claims_dict['given_name']
        dateOfBirth = claims_dict['birth_date']
        portrait = claims_dict['portrait']

        print(portrait)

        validation = False
        program = session['program']
        registration_method = 'E-ID'

        # Create a new record
        new_registered = Registered(
            name=name,
            surname=surname,
            dateOfBirth=dateOfBirth,
            program=program,
            validation=validation,
            registration_method=registration_method,
            portrait=portrait
        )
        db.session.add(new_registered)
        db.session.commit() 
    
    return {"state": state}


@app.route('/validation', methods=['GET', 'POST'])
def validation():
    accessToken = get_api_key()
    connection = http.client.HTTPSConnection(host='api.trial.procivis-one.com')
    
    baseHeaders = {
        'Accept': 'application/json',
        'Content-Type': 'application/json', 
        'Authorization': f'Bearer {accessToken}' 
        }
    proofPayload = json.dumps({
                "proofSchemaId": "ef5f9810-3eb0-4700-acc0-c0fbd36db604",
                "verifier": "b92bf54c-e91e-4537-94d6-bf804649bf0a",
                "protocol": "OPENID4VP_DRAFT20_SWIYU"
        })
    
    connection.request("POST", "/api/proof-request/v1", proofPayload, baseHeaders)
    proofCreatedResponse = connection.getresponse()
    proofCreated = proofCreatedResponse.read().decode("utf-8")

    print(proofCreated)

    proofId = json.loads(proofCreated)['id']
             
    print(proofId)

    proofRequestEndpoint = f"/api/proof-request/v1/{proofId}/share"
    connection.request("POST", proofRequestEndpoint, '', baseHeaders)
    proofRequestResponse = connection.getresponse()
    proofRequest = proofRequestResponse.read().decode("utf-8")
    print(proofRequest)
    
    url = json.loads(proofRequest)['url']

    # Generate QR code
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Convert image to base64
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return render_template('validation.html', qr_code_base64=qr_base64,  proof_id=proofId)

@app.route('/validation/status/<proof_id>')
def proof_status(proof_id):
    print("Status request..." + proof_id)
    accessToken = get_api_key()
    connection = http.client.HTTPSConnection(host='api.trial.procivis-one.com')
    
    baseHeaders = {
        'Accept': 'application/json',
        'Content-Type': 'application/json', 
        'Authorization': f'Bearer {accessToken}' 
    }

    proofRequestsEndpoint = f"/api/proof-request/v1/{proof_id}"
    connection.request("GET", proofRequestsEndpoint, '', baseHeaders)
    proofRequestsResponse = connection.getresponse()
    proofRequests = proofRequestsResponse.read().decode("utf-8")
    
    state = json.loads(proofRequests)['state']
    return {"state": state}

@app.route('/mz-validated/<proof_id>')
def mz_validated(proof_id):
    #TODO get claims and compare to DB
    accessToken = get_api_key()
    connection = http.client.HTTPSConnection(host='api.trial.procivis-one.com')
    
    baseHeaders = {
        'Accept': 'application/json',
        'Content-Type': 'application/json', 
        'Authorization': f'Bearer {accessToken}' 
    }

    proofRequestsEndpoint = f"/api/proof-request/v1/{proof_id}"
    connection.request("GET", proofRequestsEndpoint, '', baseHeaders)
    proofRequestsResponse = connection.getresponse()
    proofRequests = proofRequestsResponse.read().decode("utf-8")

    data = json.loads(proofRequests)
    # Get the first proof input
    proof_input = data['proofInputs'][0]
    # Create a dictionary of key-value pairs
    claims_dict = {claim['schema']['key']: claim['value'] for claim in proof_input['claims']}

    name = claims_dict['Vorname']
    surname = claims_dict['Nachname']
    dateOfBirth = claims_dict['Geburtsdatum']

    dateOfBirth = to_isoformat(dateOfBirth)

    print(dateOfBirth)
    
    #TODO also compare date of Birth or Heimatort
    registered = Registered.query.filter(
        func.lower(Registered.name) == surname.lower(),
        func.lower(Registered.surname) == name.lower(),
        Registered.dateOfBirth == dateOfBirth
    ).first()

    if registered:
        registered.validation = True

        db.session.commit()

        return render_template('mz-validated.html',status='success', id=registered.id ,prompt=_('Maturazeugnis erfolgreich validiert'))
    else:
        return render_template('mz-validated.html',status='warning', prompt=_('Es konnte keine passende Registration gefunden werden'))
    
@app.route('/issue-study-card/<id>')
def issue_study_card(id):
    accessToken = get_api_key()

    registered = Registered.query.get(id)

    if datetime.fromisoformat(registered.dateOfBirth).year < 1900:
        return render_template('student-card.html', error=_("Geburtsdatum ungültig"))

    matriculation_number = f"25-{random.randint(100, 999)}-{random.randint(100, 999)}"
    barcode = random.randint(1000000, 9999999)
    expiry_date = date.today() + timedelta(days=180)
    expiry_date= expiry_date.isoformat() 

    connection = http.client.HTTPSConnection(host='api.trial.procivis-one.com')
                
    baseHeaders = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {accessToken}' 
    }    

    credentialPayload = json.dumps({
        "credentialSchemaId": "d7b09ef6-6f30-4fc0-b24f-21af2c6dcfbe",
        "issuer": "b92bf54c-e91e-4537-94d6-bf804649bf0a",
        "protocol": "OPENID4VCI_DRAFT13_SWIYU",
        "claimValues": [
            {
                "claimId": "130d6d93-032a-4876-9dc8-c55752544f53",
                "path": "matriculation_number",
                "value": matriculation_number
            },
            {
                "claimId": "2b8b082d-1966-47f4-8355-cd2eef8afaa2",
                "path": "portrait",
                "value": registered.portrait
            },
            {
                "claimId": "808e602b-a1e5-4fb9-be8c-0812f207c89a",
                "path": "given_name",
                "value": str(registered.name)
            },
            {
                "claimId": "eba4ce0b-bda9-4414-8e8e-fd810c42148e",
                "path": "family_name",
                "value": str(registered.surname)
            },
            {
                "claimId": "c9fce3df-c352-405a-8262-b9cd4fe2713c",
                "path": "birth_date",
                "value": registered.dateOfBirth
            },
            {
                "claimId": "a95d3c70-1e1c-4b94-9577-6ebc5bdf823a",
                "path": "expiry_date",
                "value": expiry_date
            },
            {
                "claimId": "4857d341-fe91-4323-b7bd-307598fa7fa1",
                "path": "is_active_student",
                "value": "true"
            },
            {
                "claimId": "5d5cc6b3-3c08-4a5f-92ac-db49afcfeb52",
                "path": "Barcode",
                "value": barcode
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
    print(credentialCreated)   
    credentialId = json.loads(credentialCreated)['id']    

    issuingCredentialEndpoint = f"/api/credential/v1/{credentialId}/share"
    connection.request("POST", issuingCredentialEndpoint, '', baseHeaders)
    credentialIssuedResponse = connection.getresponse()
    credentialIssued = credentialIssuedResponse.read().decode("utf-8")
    print(credentialIssued)
    
    url = json.loads(credentialIssued)['url']
        
    # Generate QR code
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Convert image to base64
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return render_template('student-card.html', name=registered.name, surname=registered.surname, qr_code_base64=qr_base64)

@app.route('/loading')
def laden():
    return render_template('loading-1.html')  

@app.route('/validieren/<proof_id>')
def validieren(proof_id):
    return render_template('loading-2.html', proof_id=proof_id)         


if __name__ == '__main__':
    app.run(debug=True)