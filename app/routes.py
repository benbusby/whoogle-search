from app import app
from app.filter import Filter, get_first_link
from app.models.config import Config
from app.request import Request, gen_query
import argparse
from bs4 import BeautifulSoup
from cryptography.fernet import Fernet, InvalidToken
from flask import g, make_response, request, redirect, render_template, send_file
import io
import json
import os
import urllib.parse as urlparse
import waitress

app.config['APP_ROOT'] = os.getenv('APP_ROOT', os.path.dirname(os.path.abspath(__file__)))
app.config['STATIC_FOLDER'] = os.getenv('STATIC_FOLDER', os.path.join(app.config['APP_ROOT'], 'static'))

CONFIG_PATH = os.getenv('CONFIG_VOLUME', app.config['STATIC_FOLDER']) + '/config.json'


@app.before_request
def before_request_func():
    # Always redirect to https if HTTPS_ONLY is set (otherwise default to false)
    https_only = os.getenv('HTTPS_ONLY', False)

    if https_only and request.url.startswith('http://'):
        url = request.url.replace('http://', 'https://', 1)
        code = 308
        return redirect(url, code=code)

    json_config = json.load(open(CONFIG_PATH)) if os.path.exists(CONFIG_PATH) else {'url': request.url_root}
    g.user_config = Config(**json_config)

    if not g.user_config.url:
        g.user_config.url = request.url_root.replace('http://', 'https://') if https_only else request.url_root

    g.user_request = Request(request.headers.get('User-Agent'), language=g.user_config.lang)
    g.app_location = g.user_config.url


@app.errorhandler(404)
def unknown_page(e):
    return redirect(g.app_location)


@app.route('/', methods=['GET'])
def index():
    bg = '#000' if g.user_config.dark else '#fff'
    return render_template('index.html',
                           bg=bg,
                           ua=g.user_request.modified_user_agent,
                           languages=Config.LANGUAGES,
                           current_lang=g.user_config.lang,
                           request_type='get' if g.user_config.get_only else 'post')


@app.route('/opensearch.xml', methods=['GET'])
def opensearch():
    opensearch_url = g.app_location
    if opensearch_url.endswith('/'):
        opensearch_url = opensearch_url[:-1]

    template = render_template('opensearch.xml',
                               main_url=opensearch_url,
                               request_type='get' if g.user_config.get_only else 'post')
    response = make_response(template)
    response.headers['Content-Type'] = 'application/xml'
    return response


@app.route('/search', methods=['GET', 'POST'])
def search():
    request_params = request.args if request.method == 'GET' else request.form
    q = request_params.get('q')
    
    if q is None or len(q) == 0:
        return redirect('/')
    else:
        # Attempt to decrypt if this is an internal link
        try:
            q = Fernet(app.secret_key).decrypt(q.encode()).decode()
        except InvalidToken:
            pass

    feeling_lucky = q.startswith('! ')

    if feeling_lucky: # Well do you, punk?
        q = q[2:]

    user_agent = request.headers.get('User-Agent')
    mobile = 'Android' in user_agent or 'iPhone' in user_agent

    content_filter = Filter(mobile, g.user_config, secret_key=app.secret_key)
    full_query = gen_query(q, request_params, content_filter.near, language=g.user_config.lang)
    get_body = g.user_request.send(query=full_query)

    results = content_filter.reskin(get_body)
    dirty_soup = BeautifulSoup(results, 'html.parser')

    if feeling_lucky:
        redirect_url = get_first_link(dirty_soup)
        return redirect(redirect_url, 303) # Using 303 so the browser performs a GET request for the URL
    else:
        formatted_results = content_filter.clean(dirty_soup)



    return render_template('display.html', query=urlparse.unquote(q), response=formatted_results)


@app.route('/config', methods=['GET', 'POST'])
def config():
    if request.method == 'GET':
        return json.dumps(g.user_config.__dict__)
    else:
        config_data = request.form.to_dict()
        if 'url' not in config_data or not config_data['url']:
            config_data['url'] = g.user_config.url

        with open(CONFIG_PATH, 'w') as config_file:
            config_file.write(json.dumps(config_data, indent=4))
            config_file.close()

        return redirect(config_data['url'])


@app.route('/url', methods=['GET'])
def url():
    if 'url' in request.args:
        return redirect(request.args.get('url'))

    q = request.args.get('q')
    if len(q) > 0 and 'http' in q:
        return redirect(q)
    else:
        return render_template('error.html', query=q)


@app.route('/imgres')
def imgres():
    return redirect(request.args.get('imgurl'))


@app.route('/tmp')
def tmp():
    cipher_suite = Fernet(app.secret_key)
    img_url = cipher_suite.decrypt(request.args.get('image_url').encode()).decode()
    file_data = g.user_request.send(base_url=img_url, return_bytes=True)
    tmp_mem = io.BytesIO()
    tmp_mem.write(file_data)
    tmp_mem.seek(0)

    return send_file(
        tmp_mem,
        as_attachment=True,
        attachment_filename='tmp.png',
        mimetype='image/png'
    )


@app.route('/window')
def window():
    get_body = g.user_request.send(base_url=request.args.get('location'))
    get_body = get_body.replace('src="/', 'src="' + request.args.get('location') + '"')
    get_body = get_body.replace('href="/', 'href="' + request.args.get('location') + '"')

    results = BeautifulSoup(get_body, 'html.parser')

    try:
        for script in results('script'):
            script.decompose()
    except Exception:
        pass

    return render_template('display.html', response=results)


def run_app():
    parser = argparse.ArgumentParser(description='Whoogle Search console runner')
    parser.add_argument('--port', default=5000, metavar='<port number>',
                        help='Specifies a port to run on (default 5000)')
    parser.add_argument('--host', default='127.0.0.1', metavar='<ip address>',
                        help='Specifies the host address to use (default 127.0.0.1)')
    parser.add_argument('--debug', default=False, action='store_true',
                        help='Activates debug mode for the server (default False)')
    parser.add_argument('--https-only', default=False, action='store_true',
                        help='Enforces HTTPS redirects for all requests')
    args = parser.parse_args()
    os.environ['HTTPS_ONLY'] = '1' if args.https_only else ''

    if args.debug:
        app.run(host=args.host, port=args.port, debug=args.debug)
    else:
        waitress.serve(app, listen="{}:{}".format(args.host, args.port))
