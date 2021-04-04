from app.request import send_tor_signal
from app.utils.session_utils import generate_user_keys
from app.utils.gen_ddg_bangs import gen_bangs_json
from flask import Flask
from flask_session import Session
import json
import os
from stem import Signal

app = Flask(__name__, static_folder=os.path.dirname(
    os.path.abspath(__file__)) + '/static')
app.user_elements = {}
app.default_key_set = generate_user_keys()
app.no_cookie_ips = []
app.config['SECRET_KEY'] = os.urandom(32)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['VERSION_NUMBER'] = '0.3.2'
app.config['APP_ROOT'] = os.getenv(
    'APP_ROOT',
    os.path.dirname(os.path.abspath(__file__)))
app.config['LANGUAGES'] = json.load(open(
    os.path.join(app.config['APP_ROOT'], 'misc/languages.json')))
app.config['COUNTRIES'] = json.load(open(
    os.path.join(app.config['APP_ROOT'], 'misc/countries.json')))
app.config['STATIC_FOLDER'] = os.getenv(
    'STATIC_FOLDER',
    os.path.join(app.config['APP_ROOT'], 'static'))
app.config['CONFIG_PATH'] = os.getenv(
    'CONFIG_VOLUME',
    os.path.join(app.config['STATIC_FOLDER'], 'config'))
app.config['DEFAULT_CONFIG'] = os.path.join(
    app.config['CONFIG_PATH'],
    'config.json')
app.config['SESSION_FILE_DIR'] = os.path.join(
    app.config['CONFIG_PATH'],
    'session')
app.config['BANG_PATH'] = os.getenv(
    'CONFIG_VOLUME',
    os.path.join(app.config['STATIC_FOLDER'], 'bangs'))
app.config['BANG_FILE'] = os.path.join(
    app.config['BANG_PATH'],
    'bangs.json')

if not os.path.exists(app.config['CONFIG_PATH']):
    os.makedirs(app.config['CONFIG_PATH'])

if not os.path.exists(app.config['SESSION_FILE_DIR']):
    os.makedirs(app.config['SESSION_FILE_DIR'])

# Generate DDG bang filter, and create path if it doesn't exist yet
if not os.path.exists(app.config['BANG_PATH']):
    os.makedirs(app.config['BANG_PATH'])
if not os.path.exists(app.config['BANG_FILE']):
    gen_bangs_json(app.config['BANG_FILE'])

Session(app)

# Attempt to acquire tor identity, to determine if Tor config is available
send_tor_signal(Signal.HEARTBEAT)

from app import routes  # noqa
