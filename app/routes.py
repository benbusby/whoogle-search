import argparse
import base64
import io
import json
import os
import pickle
import re
import urllib.parse as urlparse
import uuid
import validators
from datetime import datetime, timedelta
from functools import wraps

import waitress
from app import app
from app.models.config import Config
from app.models.endpoint import Endpoint
from app.request import Request, TorError
from app.utils.bangs import resolve_bang
from app.utils.misc import empty_gif, placeholder_img, get_proxy_host_url, \
    fetch_favicon
from app.filter import Filter
from app.utils.misc import read_config_bool, get_client_ip, get_request_url, \
    check_for_update, encrypt_string
from app.utils.widgets import *
from app.utils.results import bold_search_terms,\
    add_currency_card, check_currency, get_tabs_content
from app.utils.search import Search, needs_https, has_captcha
from app.utils.session import valid_user_session
from bs4 import BeautifulSoup as bsoup
from flask import jsonify, make_response, request, redirect, render_template, \
    send_file, session, url_for, g
from requests import exceptions
from requests.models import PreparedRequest
from cryptography.fernet import Fernet, InvalidToken
from cryptography.exceptions import InvalidSignature
from werkzeug.datastructures import MultiDict

# Load DDG bang json files only on init
bang_json = json.load(open(app.config['BANG_FILE'])) or {}

ac_var = 'WHOOGLE_AUTOCOMPLETE'
autocomplete_enabled = os.getenv(ac_var, '1')


def get_search_name(tbm):
    for tab in app.config['HEADER_TABS'].values():
        if tab['tbm'] == tbm:
            return tab['name']


def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # do not ask password if cookies already present
        if (
            valid_user_session(session)
            and 'cookies_disabled' not in request.args
            and session['auth']
        ):
            return f(*args, **kwargs)

        auth = request.authorization

        # Skip if username/password not set
        whoogle_user = os.getenv('WHOOGLE_USER', '')
        whoogle_pass = os.getenv('WHOOGLE_PASS', '')
        if (not whoogle_user or not whoogle_pass) or (
                auth
                and whoogle_user == auth.username
                and whoogle_pass == auth.password):
            session['auth'] = True
            return f(*args, **kwargs)
        else:
            return make_response('Not logged in', 401, {
                'WWW-Authenticate': 'Basic realm="Login Required"'})

    return decorated


def session_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not valid_user_session(session):
            session.pop('_permanent', None)

        # Note: This sets all requests to use the encryption key determined per
        # instance on app init. This can be updated in the future to use a key
        # that is unique for their session (session['key']) but this should use
        # a config setting to enable the session based key. Otherwise there can
        # be problems with searches performed by users with cookies blocked if
        # a session based key is always used.
        g.session_key = app.enc_key

        # Clear out old sessions
        invalid_sessions = []
        for user_session in os.listdir(app.config['SESSION_FILE_DIR']):
            file_path = os.path.join(
                app.config['SESSION_FILE_DIR'],
                user_session)

            try:
                # Ignore files that are larger than the max session file size
                if os.path.getsize(file_path) > app.config['MAX_SESSION_SIZE']:
                    continue

                with open(file_path, 'rb') as session_file:
                    _ = pickle.load(session_file)
                    data = pickle.load(session_file)
                    if isinstance(data, dict) and 'valid' in data:
                        continue
                    invalid_sessions.append(file_path)
            except Exception:
                # Broad exception handling here due to how instances installed
                # with pip seem to have issues storing unrelated files in the
                # same directory as sessions
                pass

        for invalid_session in invalid_sessions:
            try:
                os.remove(invalid_session)
            except FileNotFoundError:
                # Don't throw error if the invalid session has been removed
                pass

        return f(*args, **kwargs)

    return decorated


@app.before_request
def before_request_func():
    global bang_json
    session.permanent = True

    # Check for latest version if needed
    now = datetime.now()
    if now - timedelta(hours=24) > app.config['LAST_UPDATE_CHECK']:
        app.config['LAST_UPDATE_CHECK'] = now
        app.config['HAS_UPDATE'] = check_for_update(
            app.config['RELEASES_URL'],
            app.config['VERSION_NUMBER'])

    g.request_params = (
        request.args if request.method == 'GET' else request.form
    )

    default_config = json.load(open(app.config['DEFAULT_CONFIG'])) \
        if os.path.exists(app.config['DEFAULT_CONFIG']) else {}

    # Generate session values for user if unavailable
    if not valid_user_session(session):
        session['config'] = default_config
        session['uuid'] = str(uuid.uuid4())
        session['key'] = app.enc_key
        session['auth'] = False

    # Establish config values per user session
    g.user_config = Config(**session['config'])

    # Update user config if specified in search args
    g.user_config = g.user_config.from_params(g.request_params)

    if not g.user_config.url:
        g.user_config.url = get_request_url(request.url_root)

    g.user_request = Request(
        request.headers.get('User-Agent'),
        get_request_url(request.url_root),
        config=g.user_config)

    g.app_location = g.user_config.url

    # Attempt to reload bangs json if not generated yet
    if not bang_json and os.path.getsize(app.config['BANG_FILE']) > 4:
        try:
            bang_json = json.load(open(app.config['BANG_FILE']))
        except json.decoder.JSONDecodeError:
            # Ignore decoding error, can occur if file is still
            # being written
            pass


@app.after_request
def after_request_func(resp):
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    resp.headers['X-Frame-Options'] = 'DENY'
    resp.headers['Cache-Control'] = 'max-age=86400'

    if os.getenv('WHOOGLE_CSP', False):
        resp.headers['Content-Security-Policy'] = app.config['CSP']
        if os.environ.get('HTTPS_ONLY', False):
            resp.headers['Content-Security-Policy'] += \
                'upgrade-insecure-requests'

    return resp


@app.errorhandler(404)
def unknown_page(e):
    app.logger.warn(e)
    return redirect(g.app_location)


@app.route(f'/{Endpoint.healthz}', methods=['GET'])
def healthz():
    return ''


@app.route('/', methods=['GET'])
@app.route(f'/{Endpoint.home}', methods=['GET'])
@auth_required
def index():
    # Redirect if an error was raised
    if 'error_message' in session and session['error_message']:
        error_message = session['error_message']
        session['error_message'] = ''
        return render_template('error.html', error_message=error_message)

    return render_template('index.html',
                           has_update=app.config['HAS_UPDATE'],
                           languages=app.config['LANGUAGES'],
                           countries=app.config['COUNTRIES'],
                           time_periods=app.config['TIME_PERIODS'],
                           themes=app.config['THEMES'],
                           autocomplete_enabled=autocomplete_enabled,
                           translation=app.config['TRANSLATIONS'][
                               g.user_config.get_localization_lang()
                           ],
                           logo=render_template(
                               'logo.html',
                               dark=g.user_config.dark),
                           config_disabled=(
                                   app.config['CONFIG_DISABLE'] or
                                   not valid_user_session(session)),
                           config=g.user_config,
                           tor_available=int(os.environ.get('TOR_AVAILABLE')),
                           version_number=app.config['VERSION_NUMBER'])


@app.route(f'/{Endpoint.opensearch}', methods=['GET'])
def opensearch():
    opensearch_url = g.app_location
    if opensearch_url.endswith('/'):
        opensearch_url = opensearch_url[:-1]

    # Enforce https for opensearch template
    if needs_https(opensearch_url):
        opensearch_url = opensearch_url.replace('http://', 'https://', 1)

    get_only = g.user_config.get_only or 'Chrome' in request.headers.get(
        'User-Agent')

    return render_template(
        'opensearch.xml',
        main_url=opensearch_url,
        request_type='' if get_only else 'method="post"',
        search_type=request.args.get('tbm'),
        search_name=get_search_name(request.args.get('tbm'))
    ), 200, {'Content-Type': 'application/xml'}


@app.route(f'/{Endpoint.search_html}', methods=['GET'])
def search_html():
    search_url = g.app_location
    if search_url.endswith('/'):
        search_url = search_url[:-1]
    return render_template('search.html', url=search_url)


@app.route(f'/{Endpoint.autocomplete}', methods=['GET', 'POST'])
def autocomplete():
    if os.getenv(ac_var) and not read_config_bool(ac_var):
        return jsonify({})

    q = g.request_params.get('q')
    if not q:
        # FF will occasionally (incorrectly) send the q field without a
        # mimetype in the format "b'q=<query>'" through the request.data field
        q = str(request.data).replace('q=', '')

    # Search bangs if the query begins with "!", but not "! " (feeling lucky)
    if q.startswith('!') and len(q) > 1 and not q.startswith('! '):
        return jsonify([q, [bang_json[_]['suggestion'] for _ in bang_json if
                            _.startswith(q)]])

    if not q and not request.data:
        return jsonify({'?': []})
    elif request.data:
        q = urlparse.unquote_plus(
            request.data.decode('utf-8').replace('q=', ''))

    # Return a list of suggestions for the query
    #
    # Note: If Tor is enabled, this returns nothing, as the request is
    # almost always rejected
    return jsonify([
        q,
        g.user_request.autocomplete(q) if not g.user_config.tor else []
    ])

@app.route(f'/{Endpoint.search}', methods=['GET', 'POST'])
@session_required
@auth_required
def search():
    if request.method == 'POST':
        # Redirect as a GET request with an encrypted query
        post_data = MultiDict(request.form)
        post_data['q'] = encrypt_string(g.session_key, post_data['q'])
        get_req_str = urlparse.urlencode(post_data)
        return redirect(url_for('.search') + '?' + get_req_str)

    search_util = Search(request, g.user_config, g.session_key)
    query = search_util.new_search_query()

    bang = resolve_bang(query, bang_json)
    if bang:
        return redirect(bang)

    # Redirect to home if invalid/blank search
    if not query:
        return redirect(url_for('.index'))

    # Generate response and number of external elements from the page
    try:
        response = search_util.generate_response()
    except TorError as e:
        session['error_message'] = e.message + (
            "\\n\\nTor config is now disabled!" if e.disable else "")
        session['config']['tor'] = False if e.disable else session['config'][
            'tor']
        return redirect(url_for('.index'))

    if search_util.feeling_lucky:
        return redirect(response, code=303)

    # If the user is attempting to translate a string, determine the correct
    # string for formatting the lingva.ml url
    localization_lang = g.user_config.get_localization_lang()
    translation = app.config['TRANSLATIONS'][localization_lang]
    translate_to = localization_lang.replace('lang_', '')

    # removing st-card to only use whoogle time selector
    soup = bsoup(response, "html.parser");
    for x in soup.find_all(attrs={"id": "st-card"}):
        x.replace_with("")

    response = str(soup)

    # Return 503 if temporarily blocked by captcha
    if has_captcha(str(response)):
        app.logger.error('503 (CAPTCHA)')
        return render_template(
            'error.html',
            blocked=True,
            error_message=translation['ratelimit'],
            translation=translation,
            farside='https://farside.link',
            config=g.user_config,
            query=urlparse.unquote(query),
            params=g.user_config.to_params(keys=['preferences'])), 503

    response = bold_search_terms(response, query)

    # check for widgets and add if requested
    if search_util.widget != '':
        html_soup = bsoup(str(response), 'html.parser')
        if search_util.widget == 'ip':
            response = add_ip_card(html_soup, get_client_ip(request))
        elif search_util.widget == 'calculator' and not 'nojs' in request.args:
            response = add_calculator_card(html_soup)

    # Update tabs content
    tabs = get_tabs_content(app.config['HEADER_TABS'],
                            search_util.full_query,
                            search_util.search_type,
                            g.user_config.preferences,
                            translation)

    # Feature to display currency_card
    # Since this is determined by more than just the
    # query is it not defined as a standard widget
    conversion = check_currency(str(response))
    if conversion:
        html_soup = bsoup(str(response), 'html.parser')
        response = add_currency_card(html_soup, conversion)

    preferences = g.user_config.preferences
    home_url = f"home?preferences={preferences}" if preferences else "home"
    cleanresponse = str(response).replace("andlt;","&lt;").replace("andgt;","&gt;")

    return render_template(
        'display.html',
        has_update=app.config['HAS_UPDATE'],
        query=urlparse.unquote(query),
        search_type=search_util.search_type,
        search_name=get_search_name(search_util.search_type),
        config=g.user_config,
        autocomplete_enabled=autocomplete_enabled,
        lingva_url=app.config['TRANSLATE_URL'],
        translation=translation,
        translate_to=translate_to,
        translate_str=query.replace(
            'translate', ''
        ).replace(
            translation['translate'], ''
        ),
        is_translation=any(
            _ in query.lower() for _ in [translation['translate'], 'translate']
        ) and not search_util.search_type,  # Standard search queries only
        response=cleanresponse,
        version_number=app.config['VERSION_NUMBER'],
        search_header=render_template(
            'header.html',
            home_url=home_url,
            config=g.user_config,
            translation=translation,
            languages=app.config['LANGUAGES'],
            countries=app.config['COUNTRIES'],
            time_periods=app.config['TIME_PERIODS'],
            logo=render_template('logo.html', dark=g.user_config.dark),
            query=urlparse.unquote(query),
            search_type=search_util.search_type,
            mobile=g.user_request.mobile,
            tabs=tabs)).replace("  ", "")


@app.route(f'/{Endpoint.config}', methods=['GET', 'POST', 'PUT'])
@session_required
@auth_required
def config():
    config_disabled = (
            app.config['CONFIG_DISABLE'] or
            not valid_user_session(session))

    name = ''
    if 'name' in request.args:
        name = os.path.normpath(request.args.get('name'))
        if not re.match(r'^[A-Za-z0-9_.+-]+$', name):
            return make_response('Invalid config name', 400)

    if request.method == 'GET':
        return json.dumps(g.user_config.__dict__)
    elif request.method == 'PUT' and not config_disabled:
        if name:
            config_pkl = os.path.join(app.config['CONFIG_PATH'], name)
            session['config'] = (pickle.load(open(config_pkl, 'rb'))
                                 if os.path.exists(config_pkl)
                                 else session['config'])
            return json.dumps(session['config'])
        else:
            return json.dumps({})
    elif not config_disabled:
        config_data = request.form.to_dict()
        if 'url' not in config_data or not config_data['url']:
            config_data['url'] = g.user_config.url

        # Save config by name to allow a user to easily load later
        if 'name' in request.args:
            pickle.dump(
                config_data,
                open(os.path.join(
                    app.config['CONFIG_PATH'],
                    name), 'wb'))

        session['config'] = config_data
        return redirect(config_data['url'])
    else:
        return redirect(url_for('.index'), code=403)


@app.route(f'/{Endpoint.imgres}')
@session_required
@auth_required
def imgres():
    return redirect(request.args.get('imgurl'))


@app.route(f'/{Endpoint.element}')
@session_required
@auth_required
def element():
    element_url = src_url = request.args.get('url')
    if element_url.startswith('gAAAAA'):
        try:
            cipher_suite = Fernet(g.session_key)
            src_url = cipher_suite.decrypt(element_url.encode()).decode()
        except (InvalidSignature, InvalidToken) as e:
            return render_template(
                'error.html',
                error_message=str(e)), 401

    src_type = request.args.get('type')

    # Ensure requested element is from a valid domain
    domain = urlparse.urlparse(src_url).netloc
    if not validators.domain(domain):
        return send_file(io.BytesIO(empty_gif), mimetype='image/gif')

    try:
        response = g.user_request.send(base_url=src_url)

        # Display an empty gif if the requested element couldn't be retrieved
        if response.status_code != 200 or len(response.content) == 0:
            if 'favicon' in src_url:
                favicon = fetch_favicon(src_url)
                return send_file(io.BytesIO(favicon), mimetype='image/png')
            else:
                return send_file(io.BytesIO(empty_gif), mimetype='image/gif')

        file_data = response.content
        tmp_mem = io.BytesIO()
        tmp_mem.write(file_data)
        tmp_mem.seek(0)

        return send_file(tmp_mem, mimetype=src_type)
    except exceptions.RequestException:
        pass

    return send_file(io.BytesIO(empty_gif), mimetype='image/gif')


@app.route(f'/{Endpoint.window}')
@session_required
@auth_required
def window():
    target_url = request.args.get('location')
    if target_url.startswith('gAAAAA'):
        cipher_suite = Fernet(g.session_key)
        target_url = cipher_suite.decrypt(target_url.encode()).decode()

    content_filter = Filter(
        g.session_key,
        root_url=request.url_root,
        config=g.user_config)
    target = urlparse.urlparse(target_url)

    # Ensure requested URL has a valid domain
    if not validators.domain(target.netloc):
        return render_template(
            'error.html',
            error_message='Invalid location'), 400

    host_url = f'{target.scheme}://{target.netloc}'

    get_body = g.user_request.send(base_url=target_url).text

    results = bsoup(get_body, 'html.parser')
    src_attrs = ['src', 'href', 'srcset', 'data-srcset', 'data-src']

    # Parse HTML response and replace relative links w/ absolute
    for element in results.find_all():
        for attr in src_attrs:
            if not element.has_attr(attr) or not element[attr].startswith('/'):
                continue

            element[attr] = host_url + element[attr]

    # Replace or remove javascript sources
    for script in results.find_all('script', {'src': True}):
        if 'nojs' in request.args:
            script.decompose()
        else:
            content_filter.update_element_src(script, 'application/javascript')

    # Replace all possible image attributes
    img_sources = ['src', 'data-src', 'data-srcset', 'srcset']
    for img in results.find_all('img'):
        _ = [
            content_filter.update_element_src(img, 'image/png', attr=_)
            for _ in img_sources if img.has_attr(_)
        ]

    # Replace all stylesheet sources
    for link in results.find_all('link', {'href': True}):
        content_filter.update_element_src(link, 'text/css', attr='href')

    # Use anonymous view for all links on page
    for a in results.find_all('a', {'href': True}):
        a['href'] = f'{Endpoint.window}?location=' + a['href'] + (
            '&nojs=1' if 'nojs' in request.args else '')

    # Remove all iframes -- these are commonly used inside of <noscript> tags
    # to enforce loading Google Analytics
    for iframe in results.find_all('iframe'):
        iframe.decompose()

    return render_template(
        'display.html',
        response=results,
        translation=app.config['TRANSLATIONS'][
            g.user_config.get_localization_lang()
        ]
    )


@app.route(f'/robots.txt')
def robots():
    response = make_response(
'''User-Agent: *
Disallow: /''', 200)
    response.mimetype = 'text/plain'
    return response


@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_message=str(e)), 404


def run_app() -> None:
    parser = argparse.ArgumentParser(
        description='Whoogle Search console runner')
    parser.add_argument(
        '--port',
        default=5000,
        metavar='<port number>',
        help='Specifies a port to run on (default 5000)')
    parser.add_argument(
        '--host',
        default='127.0.0.1',
        metavar='<ip address>',
        help='Specifies the host address to use (default 127.0.0.1)')
    parser.add_argument(
        '--unix-socket',
        default='',
        metavar='</path/to/unix.sock>',
        help='Listen for app on unix socket instead of host:port')
    parser.add_argument(
        '--debug',
        default=False,
        action='store_true',
        help='Activates debug mode for the server (default False)')
    parser.add_argument(
        '--https-only',
        default=False,
        action='store_true',
        help='Enforces HTTPS redirects for all requests')
    parser.add_argument(
        '--userpass',
        default='',
        metavar='<username:password>',
        help='Sets a username/password basic auth combo (default None)')
    parser.add_argument(
        '--proxyauth',
        default='',
        metavar='<username:password>',
        help='Sets a username/password for a HTTP/SOCKS proxy (default None)')
    parser.add_argument(
        '--proxytype',
        default='',
        metavar='<socks4|socks5|http>',
        help='Sets a proxy type for all connections (default None)')
    parser.add_argument(
        '--proxyloc',
        default='',
        metavar='<location:port>',
        help='Sets a proxy location for all connections (default None)')
    args = parser.parse_args()

    if args.userpass:
        user_pass = args.userpass.split(':')
        os.environ['WHOOGLE_USER'] = user_pass[0]
        os.environ['WHOOGLE_PASS'] = user_pass[1]

    if args.proxytype and args.proxyloc:
        if args.proxyauth:
            proxy_user_pass = args.proxyauth.split(':')
            os.environ['WHOOGLE_PROXY_USER'] = proxy_user_pass[0]
            os.environ['WHOOGLE_PROXY_PASS'] = proxy_user_pass[1]
        os.environ['WHOOGLE_PROXY_TYPE'] = args.proxytype
        os.environ['WHOOGLE_PROXY_LOC'] = args.proxyloc

    if args.https_only:
        os.environ['HTTPS_ONLY'] = '1'

    if args.debug:
        app.run(host=args.host, port=args.port, debug=args.debug)
    elif args.unix_socket:
        waitress.serve(app, unix_socket=args.unix_socket)
    else:
        waitress.serve(
            app,
            listen="{}:{}".format(args.host, args.port),
            url_prefix=os.environ.get('WHOOGLE_URL_PREFIX', ''))
