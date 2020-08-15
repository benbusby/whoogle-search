from app.utils.session_utils import generate_user_keys
from flask import Flask
from flask_session import Session
import os

app = Flask(__name__, static_folder=os.path.dirname(os.path.abspath(__file__)) + '/static')
app.user_elements = {}
app.default_key_set = generate_user_keys()
app.no_cookie_ips = []
app.config['SECRET_KEY'] = os.urandom(32)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['VERSION_NUMBER'] = '0.2.1'
app.config['APP_ROOT'] = os.getenv('APP_ROOT', os.path.dirname(os.path.abspath(__file__)))
app.config['STATIC_FOLDER'] = os.getenv('STATIC_FOLDER', os.path.join(app.config['APP_ROOT'], 'static'))
app.config['CONFIG_PATH'] = os.getenv('CONFIG_VOLUME', os.path.join(app.config['STATIC_FOLDER'], 'config'))
app.config['DEFAULT_CONFIG'] = os.path.join(app.config['CONFIG_PATH'], 'config.json')
app.config['SESSION_FILE_DIR'] = os.path.join(app.config['CONFIG_PATH'], 'session')

if not os.path.exists(app.config['CONFIG_PATH']):
    os.makedirs(app.config['CONFIG_PATH'])

if not os.path.exists(app.config['SESSION_FILE_DIR']):
    os.makedirs(app.config['SESSION_FILE_DIR'])

Session(app)

from app import routes
