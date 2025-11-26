# Github Repo for the Prototype Digital Maturity Certificate

The prototype for issuing a digital maturity certificate und registering at a sample university is currently hosted under: 

https://dmz.educa.ch/overview

# Build Information
The prototype is built on the APIs provided by Procivis and the product Procivis One Desk.

To run the entire project yourself, you need at least one access key and a client secret. The client secret is currently embedded in the code and must be replaced in the function get_api_key().

## Setup and Installation
To run this app, you need to have Python 3 installed on your computer. You can download Python 3 from the official Python website: https://www.python.org/downloads/. Make sure pip is installed.

Create a virtual environment with: 

```
python3 -m venv env

```
and activate it with:

```
source env/bin/activate
```

Once you have installed Python 3, you need to install the required packages in the virtual environement by running the following command in your terminal or command prompt:

```
pip install -r requirements.txt
```

After installing the required packages, you can run the app by running the following command in your terminal or command prompt: 

```
python app.py
```

This will start the Flask development server and make the app available at http://localhost:5000/. You can then access the app by navigating to that URL in your web browser.

# Run on Server
The app is prepared to run on a server. There activate the virtual environment and run:

```
gunicorn app:app -c gunicorn.conf.py --log-level=debug &
```

# Translations
The translations in the app are done using babel. To change the translated content or to add another language run the following commands. To collect all translatable content run:
```
pybabel extract -F babel.cfg -o messages.pot templates/* app.py 
```
Then run the following command to update the translation file.

```
pybabel update -i messages.pot -d translations
```

Now translate all content to the selective language and compile using:
```
pybabel compile -d translations
```