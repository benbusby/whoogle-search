from app.filter import clean_query
from app.request import send_tor_signal
from app.utils.session import generate_key
from app.utils.bangs import gen_bangs_json, load_all_bangs
from app.utils.misc import gen_file_hash, read_config_bool
from app.utils.ua_generator import load_ua_pool
from base64 import b64encode
from bs4 import MarkupResemblesLocatorWarning
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask
import json
import logging.config
import os
import sys
from stem import Signal
import threading
import warnings

from werkzeug.middleware.proxy_fix import ProxyFix

from app.services.http_client import HttpxClient
from app.services.provider import close_all_clients
from app.version import __version__

app = Flask(__name__, static_folder=os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'static'))

app.wsgi_app = ProxyFix(app.wsgi_app)

# look for WHOOGLE_ENV, else look in parent directory
dot_env_path = os.getenv(
    "WHOOGLE_DOTENV_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "../whoogle.env"))

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
app.config['BUNDLE_STATIC'] = read_config_bool('WHOOGLE_BUNDLE_STATIC')
with open(os.path.join(app.config['STATIC_FOLDER'], 'settings/languages.json'), 'r', encoding='utf-8') as f:
    app.config['LANGUAGES'] = json.load(f)
with open(os.path.join(app.config['STATIC_FOLDER'], 'settings/countries.json'), 'r', encoding='utf-8') as f:
    app.config['COUNTRIES'] = json.load(f)
with open(os.path.join(app.config['STATIC_FOLDER'], 'settings/time_periods.json'), 'r', encoding='utf-8') as f:
    app.config['TIME_PERIODS'] = json.load(f)
with open(os.path.join(app.config['STATIC_FOLDER'], 'settings/translations.json'), 'r', encoding='utf-8') as f:
    app.config['TRANSLATIONS'] = json.load(f)
with open(os.path.join(app.config['STATIC_FOLDER'], 'settings/themes.json'), 'r', encoding='utf-8') as f:
    app.config['THEMES'] = json.load(f)
with open(os.path.join(app.config['STATIC_FOLDER'], 'settings/header_tabs.json'), 'r', encoding='utf-8') as f:
    app.config['HEADER_TABS'] = json.load(f)
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
# Maximum session file size in bytes (4KB limit to prevent abuse and disk exhaustion)
# Session files larger than this are ignored during cleanup to avoid processing
# potentially malicious or corrupted files
app.config['MAX_SESSION_SIZE'] = 4000
app.config['BANG_PATH'] = os.getenv(
    'CONFIG_VOLUME',
    os.path.join(app.config['STATIC_FOLDER'], 'bangs'))
app.config['BANG_FILE'] = os.path.join(
    app.config['BANG_PATH'],
    'bangs.json')

# Global services registry (simple DI)
app.services = {}


@app.teardown_appcontext
def _teardown_clients(exception):
    try:
        close_all_clients()
    except Exception:
        pass

# Ensure all necessary directories exist
if not os.path.exists(app.config['CONFIG_PATH']):
    os.makedirs(app.config['CONFIG_PATH'])

if not os.path.exists(app.config['SESSION_FILE_DIR']):
    os.makedirs(app.config['SESSION_FILE_DIR'])

if not os.path.exists(app.config['BANG_PATH']):
    os.makedirs(app.config['BANG_PATH'])

if not os.path.exists(app.config['BUILD_FOLDER']):
    os.makedirs(app.config['BUILD_FOLDER'])

# Initialize User Agent pool
app.config['UA_CACHE_PATH'] = os.path.join(app.config['CONFIG_PATH'], 'ua_cache.json')
try:
    app.config['UA_POOL'] = load_ua_pool(app.config['UA_CACHE_PATH'], count=10)
except Exception as e:
    # If UA pool loading fails, log warning and set empty pool
    # The gen_user_agent function will handle the fallback
    print(f"Warning: Could not initialize UA pool: {e}")
    app.config['UA_POOL'] = []

# Session values - Secret key management
# Priority: environment variable → file → generate new
def get_secret_key():
    """Load or generate secret key with validation.
    
    Priority order:
    1. WHOOGLE_SECRET_KEY environment variable
    2. Existing key file
    3. Generate new key and save to file
    
    Returns:
        str: Valid secret key for Flask sessions
    """
    # Check environment variable first
    env_key = os.getenv('WHOOGLE_SECRET_KEY', '').strip()
    if env_key:
        # Validate env key has minimum length
        if len(env_key) >= 32:
            return env_key
        else:
            print(f"Warning: WHOOGLE_SECRET_KEY too short ({len(env_key)} chars, need 32+). Using file/generated key instead.", file=sys.stderr)
    
    # Check file-based key
    app_key_path = os.path.join(app.config['CONFIG_PATH'], 'whoogle.key')
    if os.path.exists(app_key_path):
        try:
            with open(app_key_path, 'r', encoding='utf-8') as f:
                key = f.read().strip()
                # Validate file key
                if len(key) >= 32:
                    return key
                else:
                    print(f"Warning: Key file too short, regenerating", file=sys.stderr)
        except (PermissionError, IOError) as e:
            print(f"Warning: Could not read key file: {e}", file=sys.stderr)
    
    # Generate new key
    new_key = str(b64encode(os.urandom(32)))
    try:
        with open(app_key_path, 'w', encoding='utf-8') as key_file:
            key_file.write(new_key)
    except (PermissionError, IOError) as e:
        print(f"Warning: Could not save key file: {e}. Key will not persist across restarts.", file=sys.stderr)
    
    return new_key

app.config['SECRET_KEY'] = get_secret_key()
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
generating_bangs = False
if not os.path.exists(app.config['BANG_FILE']):
    generating_bangs = True
    with open(app.config['BANG_FILE'], 'w', encoding='utf-8') as f:
        json.dump({}, f)
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

# Optionally create simple bundled assets (opt-in via WHOOGLE_BUNDLE_STATIC=1)
if app.config['BUNDLE_STATIC']:
    # CSS bundle: include all css except theme files (end with -theme.css)
    css_dir = os.path.join(app.config['STATIC_FOLDER'], 'css')
    css_parts = []
    for name in sorted(os.listdir(css_dir)):
        if not name.endswith('.css'):
            continue
        if name.endswith('-theme.css'):
            continue
        try:
            with open(os.path.join(css_dir, name), 'r', encoding='utf-8') as f:
                css_parts.append(f.read())
        except Exception:
            pass
    css_bundle = '\n'.join(css_parts)
    if css_bundle:
        css_tmp = os.path.join(app.config['BUILD_FOLDER'], 'app.css')
        with open(css_tmp, 'w', encoding='utf-8') as f:
            f.write(css_bundle)
        css_hashed = gen_file_hash(app.config['BUILD_FOLDER'], 'app.css')
        os.replace(css_tmp, os.path.join(app.config['BUILD_FOLDER'], css_hashed))
        map_path = os.path.join('app/static/build', css_hashed)
        app.config['CACHE_BUSTING_MAP']['bundle.css'] = map_path

    # JS bundle: include all js files
    js_dir = os.path.join(app.config['STATIC_FOLDER'], 'js')
    js_parts = []
    for name in sorted(os.listdir(js_dir)):
        if not name.endswith('.js'):
            continue
        try:
            with open(os.path.join(js_dir, name), 'r', encoding='utf-8') as f:
                js_parts.append(f.read())
        except Exception:
            pass
    js_bundle = '\n;'.join(js_parts)
    if js_bundle:
        js_tmp = os.path.join(app.config['BUILD_FOLDER'], 'app.js')
        with open(js_tmp, 'w', encoding='utf-8') as f:
            f.write(js_bundle)
        js_hashed = gen_file_hash(app.config['BUILD_FOLDER'], 'app.js')
        os.replace(js_tmp, os.path.join(app.config['BUILD_FOLDER'], js_hashed))
        map_path = os.path.join('app/static/build', js_hashed)
        app.config['CACHE_BUSTING_MAP']['bundle.js'] = map_path

# Templating functions
app.jinja_env.globals.update(clean_query=clean_query)
app.jinja_env.globals.update(
    cb_url=lambda f: app.config['CACHE_BUSTING_MAP'][f.lower()])
app.jinja_env.globals.update(
    bundle_static=lambda: app.config.get('BUNDLE_STATIC', False))

# Attempt to acquire tor identity, to determine if Tor config is available
send_tor_signal(Signal.HEARTBEAT)

# Suppress spurious warnings from BeautifulSoup
warnings.simplefilter('ignore', MarkupResemblesLocatorWarning)

from app import routes  # noqa

# The gen_bangs_json function takes care of loading bangs, so skip it here if
# it's already being loaded
if not generating_bangs:
    load_all_bangs(app.config['BANG_FILE'])

# Disable logging from imported modules
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': True,
})
