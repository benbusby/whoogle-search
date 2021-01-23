import argparse
import base64
import io
import json
import os
import pickle
import urllib.parse as urlparse
import uuid
from functools import wraps

import waitress
from flask import jsonify, make_response, request, redirect, render_template, \
    send_file, session, url_for
from requests import exceptions

from app import app
from app.models.config import Config
from app.request import Request, TorError
from app.utils.session_utils import valid_user_session
from app.utils.routing_utils import *

# Load DDG bang json files only on init
bang_json = json.load(open(app.config['BANG_FILE']))


def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization

        # Skip if username/password not set
        whoogle_user = os.getenv('WHOOGLE_USER', '')
        whoogle_pass = os.getenv('WHOOGLE_PASS', '')
        if (not whoogle_user or not whoogle_pass) or (
                auth
                and whoogle_user == auth.username
                and whoogle_pass == auth.password):
            return f(*args, **kwargs)
        else:
            return make_response('Not logged in', 401, {
                'WWW-Authenticate': 'Basic realm="Login Required"'})

    return decorated


@app.before_request
def before_request_func():
    g.request_params = (
        request.args if request.method == 'GET' else request.form
    )
    g.cookies_disabled = False

    # Generate session values for user if unavailable
    if not valid_user_session(session):
        session['config'] = json.load(open(app.config['DEFAULT_CONFIG'])) \
            if os.path.exists(app.config['DEFAULT_CONFIG']) else {
            'url': request.url_root}
        session['uuid'] = str(uuid.uuid4())
        session['fernet_keys'] = generate_user_keys(True)

        # Flag cookies as possibly disabled in order to prevent against
        # unnecessary session directory expansion
        g.cookies_disabled = True

    if session['uuid'] not in app.user_elements:
        app.user_elements.update({session['uuid']: 0})

    # Handle https upgrade
    if needs_https(request.url):
        return redirect(
            request.url.replace('http://', 'https://', 1),
            code=308)

    g.user_config = Config(**session['config'])

    if not g.user_config.url:
        g.user_config.url = request.url_root.replace(
            'http://',
            'https://') if os.getenv('HTTPS_ONLY', False) else request.url_root

    g.user_request = Request(
        request.headers.get('User-Agent'),
        request.url_root,
        config=g.user_config)

    g.app_location = g.user_config.url


@app.after_request
def after_request_func(response):
    if app.user_elements[session['uuid']] <= 0 and '/element' in request.url:
        # Regenerate element key if all elements have been served to user
        session['fernet_keys'][
            'element_key'] = '' if not g.cookies_disabled else \
            app.default_key_set['element_key']
        app.user_elements[session['uuid']] = 0

    # Check if address consistently has cookies blocked,
    # in which case start removing session files after creation.
    #
    # Note: This is primarily done to prevent overpopulation of session
    # directories, since browsers that block cookies will still trigger
    # Flask's session creation routine with every request.
    if g.cookies_disabled and request.remote_addr not in app.no_cookie_ips:
        app.no_cookie_ips.append(request.remote_addr)
    elif g.cookies_disabled and request.remote_addr in app.no_cookie_ips:
        session_list = list(session.keys())
        for key in session_list:
            session.pop(key)

    return response


@app.errorhandler(404)
def unknown_page(e):
    app.logger.warn(e)
    return redirect(g.app_location)


@app.route('/', methods=['GET'])
@auth_required
def index():
    # Reset keys
    session['fernet_keys'] = generate_user_keys(g.cookies_disabled)
    error_message = session[
        'error_message'] if 'error_message' in session else ''
    session['error_message'] = ''

    return render_template('index.html',
                           languages=app.config['LANGUAGES'],
                           countries=app.config['COUNTRIES'],
                           config=g.user_config,
                           error_message=error_message,
                           tor_available=int(os.environ.get('TOR_AVAILABLE')),
                           version_number=app.config['VERSION_NUMBER'])


@app.route('/opensearch.xml', methods=['GET'])
@auth_required
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
        request_type='' if get_only else 'method="post"'
    ), 200, {'Content-Disposition': 'attachment; filename="opensearch.xml"'}


@app.route('/autocomplete', methods=['GET', 'POST'])
def autocomplete():
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


@app.route('/search', methods=['GET', 'POST'])
@auth_required
def search():
    # Reset element counter
    app.user_elements[session['uuid']] = 0

    # Update user config if specified in search args
    g.user_config = g.user_config.from_params(g.request_params)

    search_util = RoutingUtils(request, g.user_config, session,
                               cookies_disabled=g.cookies_disabled)
    query = search_util.new_search_query()

    resolved_bangs = search_util.bang_operator(bang_json)
    if resolved_bangs != '':
        return redirect(resolved_bangs)

    # Redirect to home if invalid/blank search
    if not query:
        return redirect('/')

    # Generate response and number of external elements from the page
    try:
        response, elements = search_util.generate_response()
    except TorError as e:
        session['error_message'] = e.message + (
            "\\n\\nTor config is now disabled!" if e.disable else "")
        session['config']['tor'] = False if e.disable else session['config'][
            'tor']
        return redirect(url_for('.index'))

    if search_util.feeling_lucky or elements < 0:
        return redirect(response, code=303)

    # Keep count of external elements to fetch before
    # the element key can be regenerated
    app.user_elements[session['uuid']] = elements

    return render_template(
        'display.html',
        query=urlparse.unquote(query),
        search_type=search_util.search_type,
        dark_mode=g.user_config.dark,
        response=response,
        version_number=app.config['VERSION_NUMBER'],
        search_header=(render_template(
            'header.html',
            dark_mode=g.user_config.dark,
            query=urlparse.unquote(query),
            search_type=search_util.search_type,
            mobile=g.user_request.mobile)
                if 'isch' not in search_util.search_type else ''))


@app.route('/config', methods=['GET', 'POST', 'PUT'])
@auth_required
def config():
    if request.method == 'GET':
        return json.dumps(g.user_config.__dict__)
    elif request.method == 'PUT':
        if 'name' in request.args:
            config_pkl = os.path.join(
                app.config['CONFIG_PATH'],
                request.args.get('name'))
            session['config'] = (pickle.load(open(config_pkl, 'rb'))
                                 if os.path.exists(config_pkl)
                                 else session['config'])
            return json.dumps(session['config'])
        else:
            return json.dumps({})
    else:
        config_data = request.form.to_dict()
        if 'url' not in config_data or not config_data['url']:
            config_data['url'] = g.user_config.url

        # Save config by name to allow a user to easily load later
        if 'name' in request.args:
            pickle.dump(
                config_data,
                open(os.path.join(
                    app.config['CONFIG_PATH'],
                    request.args.get('name')), 'wb'))

        # Overwrite default config if user has cookies disabled
        if g.cookies_disabled:
            open(app.config['DEFAULT_CONFIG'], 'w').write(
                json.dumps(config_data, indent=4))

        session['config'] = config_data
        return redirect(config_data['url'])


@app.route('/url', methods=['GET'])
@auth_required
def url():
    if 'url' in request.args:
        return redirect(request.args.get('url'))

    q = request.args.get('q')
    if len(q) > 0 and 'http' in q:
        return redirect(q)
    else:
        return render_template('error.html', query=q)


@app.route('/imgres')
@auth_required
def imgres():
    return redirect(request.args.get('imgurl'))


@app.route('/element')
@auth_required
def element():
    cipher_suite = Fernet(session['fernet_keys']['element_key'])
    src_url = cipher_suite.decrypt(request.args.get('url').encode()).decode()
    src_type = request.args.get('type')

    try:
        file_data = g.user_request.send(base_url=src_url).content
        app.user_elements[session['uuid']] -= 1
        tmp_mem = io.BytesIO()
        tmp_mem.write(file_data)
        tmp_mem.seek(0)

        return send_file(tmp_mem, mimetype=src_type)
    except exceptions.RequestException:
        pass

    empty_gif = base64.b64decode(
        'R0lGODlhAQABAIAAAP///////yH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==')
    return send_file(io.BytesIO(empty_gif), mimetype='image/gif')


@app.route('/window')
@auth_required
def window():
    get_body = g.user_request.send(base_url=request.args.get('location')).text
    get_body = get_body.replace('src="/',
                                'src="' + request.args.get('location') + '"')
    get_body = get_body.replace('href="/',
                                'href="' + request.args.get('location') + '"')

    results = bsoup(get_body, 'html.parser')

    for script in results('script'):
        script.decompose()

    return render_template('display.html', response=results)


def run_app():
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

    os.environ['HTTPS_ONLY'] = '1' if args.https_only else ''

    if args.debug:
        app.run(host=args.host, port=args.port, debug=args.debug)
    else:
        waitress.serve(app, listen="{}:{}".format(args.host, args.port))
