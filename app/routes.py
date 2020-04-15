from app import app, rhyme
from app.filter import Filter
from bs4 import BeautifulSoup
from flask import request, redirect, render_template
from io import BytesIO
import json
import os
import pycurl
import urllib.parse as urlparse

app.config['APP_ROOT'] = os.getenv('APP_ROOT', os.path.dirname(os.path.abspath(__file__)))
app.config['STATIC_FOLDER'] = os.getenv('STATIC_FOLDER', os.path.join(app.config['APP_ROOT'], 'static'))

# Get Mozilla Firefox rhyme (important) and form a new user agent
mozilla = rhyme.get_rhyme('Mo') + 'zilla'
firefox = rhyme.get_rhyme('Fire') + 'fox'

MOBILE_UA = mozilla + '/5.0 (Android 4.20; Mobile; rv:54.0) Gecko/54.0 ' + firefox + '/59.0'
DESKTOP_UA = mozilla + '/5.0 (Windows NT 6.1; Win64; x64; rv:59.0) Gecko/20100101 Mobile ' + firefox + '/59.0'

# Base search url
SEARCH_URL = 'https://www.google.com/search?gbv=1&q='

user_config = json.load(open(app.config['STATIC_FOLDER'] + '/config.json'))


def get_ua(user_agent):
    return MOBILE_UA if ('Android' in user_agent or 'iPhone' in user_agent) else DESKTOP_UA


def send_request(curl_url, ua):
    response_header = []

    b_obj = BytesIO()
    crl = pycurl.Curl()
    crl.setopt(crl.URL, curl_url)
    crl.setopt(crl.USERAGENT, ua)
    crl.setopt(crl.WRITEDATA, b_obj)
    crl.setopt(crl.HEADERFUNCTION, response_header.append)
    crl.setopt(pycurl.FOLLOWLOCATION, 1)
    crl.perform()
    crl.close()

    return b_obj.getvalue().decode('utf-8', 'ignore')


@app.route('/', methods=['GET'])
def index():
    bg = '#000' if 'dark' in user_config and user_config['dark'] else '#fff'
    return render_template('index.html', bg=bg)


@app.route('/search', methods=['GET'])
def search():
    q = request.args.get('q')
    if q is None or len(q) <= 0:
        return render_template('error.html')

    user_agent = request.headers.get('User-Agent')
    mobile = 'Android' in user_agent or 'iPhone' in user_agent

    content_filter = Filter(mobile, user_config)
    full_query = content_filter.gen_query(q, request.args)
    get_body = send_request(SEARCH_URL + full_query, get_ua(user_agent))
    get_body = content_filter.reskin(get_body)
    soup = content_filter.clean(BeautifulSoup(get_body, 'html.parser'))

    return render_template('display.html', query=urlparse.unquote(q), response=soup)


@app.route('/config', methods=['GET', 'POST'])
def config():
    global user_config
    if request.method == 'GET':
        return json.dumps(user_config)
    else:
        with open(app.config['STATIC_FOLDER'] + '/config.json', 'w') as config_file:
            config_file.write(json.dumps(json.loads(request.data), indent=4))
            config_file.close()

            user_config = json.loads(request.data)

        return 'New config: ' + str(request.data)


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


@app.route('/window')
def window():
    get_body = send_request(request.args.get('location'), get_ua(request.headers.get('User-Agent')))
    get_body = get_body.replace('src="/', 'src="' + request.args.get('location') + '"')
    get_body = get_body.replace('href="/', 'href="' + request.args.get('location') + '"')

    soup = BeautifulSoup(get_body, 'html.parser')

    try:
        for script in soup('script'):
            script.decompose()
    except Exception:
        pass

    return render_template('display.html', response=soup)


if __name__ == '__main__':
    app.run(debug=True)
