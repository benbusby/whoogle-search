from cryptography.fernet import Fernet
from flask import Flask
import os

app = Flask(__name__, static_folder=os.path.dirname(os.path.abspath(__file__)) + '/static')
app.secret_key = Fernet.generate_key()
app.config['VERSION_NUMBER'] = '0.1.2'
app.config['APP_ROOT'] = os.getenv('APP_ROOT', os.path.dirname(os.path.abspath(__file__)))
app.config['STATIC_FOLDER'] = os.getenv('STATIC_FOLDER', os.path.join(app.config['APP_ROOT'], 'static'))
app.config['CONFIG_PATH'] = os.getenv('CONFIG_VOLUME', app.config['STATIC_FOLDER']) + '/config.json'

from app import routes
