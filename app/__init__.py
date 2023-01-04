from app.filter import clean_query
from app.request import send_tor_signal
from app.utils.session import generate_key
from app.utils.bangs import gen_bangs_json
from app.utils.misc import gen_file_hash, read_config_bool
from base64 import b64encode
from datetime import datetime, timedelta
from flask import Flask
import json
import logging.config
import os
from stem import Signal
import threading
from dotenv import load_dotenv

from werkzeug.middleware.proxy_fix import ProxyFix

from app.utils.misc import read_config_bool
from app.version import __version__

app = Flask(__name__, static_folder=os.path.dirname(
    os.path.abspath(__file__)) + '/static')

app.wsgi_app = ProxyFix(app.wsgi_app)

dot_env_path = (
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
    '../whoogle.env'))

# Load .env file if enabled
if os.path.exists(dot_env_path):
    load_dotenv(dot_env_path)

app.enc_key = generate_key()

if read_config_bool('HTTPS_ONLY'):
    app.config['SESSION_COOKIE_NAME'] = '__Secure-session'
    app.config['SESSION_COOKIE_SECURE'] = True

app.config['VERSION_NUMBER'] = __version__
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
    os.path.join(app.config['STATIC_FOLDER'], 'settings/countries.json'),
    encoding='utf-8'))
app.config['TIME_PERIODS'] = json.load(open(
    os.path.join(app.config['STATIC_FOLDER'], 'settings/time_periods.json'),
    encoding='utf-8'))
app.config['TRANSLATIONS'] = json.load(open(
    os.path.join(app.config['STATIC_FOLDER'], 'settings/translations.json'),
    encoding='utf-8'))
app.config['THEMES'] = json.load(open(
    os.path.join(app.config['STATIC_FOLDER'], 'settings/themes.json'),
    encoding='utf-8'))
app.config['HEADER_TABS'] = json.load(open(
    os.path.join(app.config['STATIC_FOLDER'], 'settings/header_tabs.json'),
    encoding='utf-8'))
app.config['CONFIG_PATH'] = os.getenv(
    'CONFIG_VOLUME',
    os.path.join(app.config['STATIC_FOLDER'], 'config'))
app.config['DEFAULT_CONFIG'] = os.path.join(
    app.config['CONFIG_PATH'],
    'config.json')
app.config['CONFIG_DISABLE'] = read_config_bool('WHOOGLE_CONFIG_DISABLE')
app.config['SESSION_FILE_DIR'] = os.path.join(
    app.config['CONFIG_PATH'],
    'session')
app.config['MAX_SESSION_SIZE'] = 4000  # Sessions won't exceed 4KB
app.config['BANG_PATH'] = os.getenv(
    'CONFIG_VOLUME',
    os.path.join(app.config['STATIC_FOLDER'], 'bangs'))
app.config['BANG_FILE'] = os.path.join(
    app.config['BANG_PATH'],
    'bangs.json')

# Ensure all necessary directories exist
if not os.path.exists(app.config['CONFIG_PATH']):
    os.makedirs(app.config['CONFIG_PATH'])

if not os.path.exists(app.config['SESSION_FILE_DIR']):
    os.makedirs(app.config['SESSION_FILE_DIR'])

if not os.path.exists(app.config['BANG_PATH']):
    os.makedirs(app.config['BANG_PATH'])

if not os.path.exists(app.config['BUILD_FOLDER']):
    os.makedirs(app.config['BUILD_FOLDER'])

# Session values
app_key_path = os.path.join(app.config['CONFIG_PATH'], 'whoogle.key')
if os.path.exists(app_key_path):
    app.config['SECRET_KEY'] = open(app_key_path, 'r').read()
else:
    app.config['SECRET_KEY'] = str(b64encode(os.urandom(32)))
    with open(app_key_path, 'w') as key_file:
        key_file.write(app.config['SECRET_KEY'])
        key_file.close()
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=365)

# NOTE: SESSION_COOKIE_SAMESITE must be set to 'lax' to allow the user's
# previous session to persist when accessing the instance from an external
# link. Setting this value to 'strict' causes Whoogle to revalidate a new
# session, and fail, resulting in cookies being disabled.
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Config fields that are used to check for updates
app.config['RELEASES_URL'] = 'https://github.com/' \
                             'benbusby/whoogle-search/releases'
app.config['LAST_UPDATE_CHECK'] = datetime.now() - timedelta(hours=24)
app.config['HAS_UPDATE'] = ''

# The alternative to Google Translate is treated a bit differently than other
# social media site alternatives, in that it is used for any translation
# related searches.
translate_url = os.getenv('WHOOGLE_ALT_TL', 'https://farside.link/lingva')
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

# Generate DDG bang filter
if not os.path.exists(app.config['BANG_FILE']):
    json.dump({}, open(app.config['BANG_FILE'], 'w'))
    bangs_thread = threading.Thread(
        target=gen_bangs_json,
        args=(app.config['BANG_FILE'],))
    bangs_thread.start()

# Build new mapping of static files for cache busting
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

# Attempt to acquire tor identity, to determine if Tor config is available
send_tor_signal(Signal.HEARTBEAT)

from app import routes  # noqa

# Disable logging from imported modules
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': True,
})
