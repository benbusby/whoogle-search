from app.filter import clean_query
from app.request import send_tor_signal
from app.utils.session import generate_user_key
from app.utils.bangs import gen_bangs_json
from app.utils.misc import gen_file_hash
from flask import Flask
from flask_session import Session
import json
import logging.config
import os
from stem import Signal
from dotenv import load_dotenv

app = Flask(__name__, static_folder=os.path.dirname(
    os.path.abspath(__file__)) + '/static')

# Load .env file if enabled
if os.getenv("WHOOGLE_DOTENV", ''):
    dotenv_path = '../whoogle.env'
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             dotenv_path))

app.default_key = generate_user_key()
app.no_cookie_ips = []
app.config['SECRET_KEY'] = os.urandom(32)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['VERSION_NUMBER'] = '0.6.0'
app.config['APP_ROOT'] = os.getenv(
    'APP_ROOT',
    os.path.dirname(os.path.abspath(__file__)))
app.config['STATIC_FOLDER'] = os.getenv(
    'STATIC_FOLDER',
    os.path.join(app.config['APP_ROOT'], 'static'))
app.config['BUILD_FOLDER'] = os.path.join(
    app.config['STATIC_FOLDER'], 'build')
app.config['CACHE_BUSTING_MAP'] = {}
app.config['LANGUAGES'] = json.load(open(
    os.path.join(app.config['STATIC_FOLDER'], 'settings/languages.json'),
    encoding='utf-8'))
app.config['COUNTRIES'] = json.load(open(
    os.path.join(app.config['STATIC_FOLDER'], 'settings/countries.json')))
app.config['TRANSLATIONS'] = json.load(open(
    os.path.join(app.config['STATIC_FOLDER'], 'settings/translations.json')))
app.config['THEMES'] = json.load(open(
    os.path.join(app.config['STATIC_FOLDER'], 'settings/themes.json')))
app.config['CONFIG_PATH'] = os.getenv(
    'CONFIG_VOLUME',
    os.path.join(app.config['STATIC_FOLDER'], 'config'))
app.config['DEFAULT_CONFIG'] = os.path.join(
    app.config['CONFIG_PATH'],
    'config.json')
app.config['CONFIG_DISABLE'] = os.getenv('WHOOGLE_CONFIG_DISABLE', '')
app.config['SESSION_FILE_DIR'] = os.path.join(
    app.config['CONFIG_PATH'],
    'session')
app.config['BANG_PATH'] = os.getenv(
    'CONFIG_VOLUME',
    os.path.join(app.config['STATIC_FOLDER'], 'bangs'))
app.config['BANG_FILE'] = os.path.join(
    app.config['BANG_PATH'],
    'bangs.json')

# The alternative to Google Translate is treated a bit differently than other
# social media site alternatives, in that it is used for any translation
# related searches.
translate_url = os.getenv('WHOOGLE_ALT_TL', 'https://lingva.ml')
if not translate_url.startswith('http'):
    translate_url = 'https://' + translate_url
app.config['TRANSLATE_URL'] = translate_url

app.config['CSP'] = 'default-src \'none\';' \
                    'frame-src ' + translate_url + ';' \
                    'manifest-src \'self\';' \
                    'img-src \'self\' data:;' \
                    'style-src \'self\' \'unsafe-inline\';' \
                    'script-src \'self\';' \
                    'media-src \'self\';' \
                    'connect-src \'self\';'

if not os.path.exists(app.config['CONFIG_PATH']):
    os.makedirs(app.config['CONFIG_PATH'])

if not os.path.exists(app.config['SESSION_FILE_DIR']):
    os.makedirs(app.config['SESSION_FILE_DIR'])

# Generate DDG bang filter, and create path if it doesn't exist yet
if not os.path.exists(app.config['BANG_PATH']):
    os.makedirs(app.config['BANG_PATH'])
if not os.path.exists(app.config['BANG_FILE']):
    gen_bangs_json(app.config['BANG_FILE'])

# Build new mapping of static files for cache busting
if not os.path.exists(app.config['BUILD_FOLDER']):
    os.makedirs(app.config['BUILD_FOLDER'])

cache_busting_dirs = ['css', 'js']
for cb_dir in cache_busting_dirs:
    full_cb_dir = os.path.join(app.config['STATIC_FOLDER'], cb_dir)
    for cb_file in os.listdir(full_cb_dir):
        # Create hash from current file state
        full_cb_path = os.path.join(full_cb_dir, cb_file)
        cb_file_link = gen_file_hash(full_cb_dir, cb_file)
        build_path = os.path.join(app.config['BUILD_FOLDER'], cb_file_link)

        try:
            os.symlink(full_cb_path, build_path)
        except FileExistsError:
            # Symlink hasn't changed, ignore
            pass

        # Create mapping for relative path urls
        map_path = build_path.replace(app.config['APP_ROOT'], '')
        if map_path.startswith('/'):
            map_path = map_path[1:]
        app.config['CACHE_BUSTING_MAP'][cb_file] = map_path

# Templating functions
app.jinja_env.globals.update(clean_query=clean_query)
app.jinja_env.globals.update(
    cb_url=lambda f: app.config['CACHE_BUSTING_MAP'][f])

Session(app)

# Attempt to acquire tor identity, to determine if Tor config is available
send_tor_signal(Signal.HEARTBEAT)

from app import routes  # noqa

# Disable logging from imported modules
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': True,
})
