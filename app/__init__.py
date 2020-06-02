from app.utils.misc import generate_user_keys
from cryptography.fernet import Fernet
from flask import Flask
from flask_session import Session
import os

app = Flask(__name__, static_folder=os.path.dirname(os.path.abspath(__file__)) + '/static')
app.user_elements = {}
app.config['SECRET_KEY'] = os.urandom(16)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['VERSION_NUMBER'] = '0.2.0'
app.config['APP_ROOT'] = os.getenv('APP_ROOT', os.path.dirname(os.path.abspath(__file__)))
app.config['STATIC_FOLDER'] = os.getenv('STATIC_FOLDER', os.path.join(app.config['APP_ROOT'], 'static'))
app.config['CONFIG_PATH'] = os.getenv('CONFIG_VOLUME', app.config['STATIC_FOLDER'] + '/config')
app.config['SESSION_FILE_DIR'] = app.config['CONFIG_PATH']
app.config['SESSION_COOKIE_SECURE'] = True

if not os.path.exists(app.config['CONFIG_PATH']):
    os.makedirs(app.config['CONFIG_PATH'])

sess = Session()
sess.init_app(app)

from app import routes
