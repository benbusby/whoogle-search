from app import app
from bs4 import BeautifulSoup
from flask import request, redirect, Response, render_template
import json
import os
import pycurl
import rhyme
import re
import urllib.parse as urlparse
from urllib.parse import parse_qs
from io import BytesIO

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC_FOLDER = os.path.join(APP_ROOT, 'static')

# Get Mozilla Firefox rhyme (important) and form a new user agent
mozilla = rhyme.get_rhyme('Mo') + 'zilla'
firefox = rhyme.get_rhyme('Fire') + 'fox'

MOBILE_UA = mozilla + '/5.0 (Android 4.20; Mobile; rv:54.0) Gecko/54.0 ' + firefox + '/59.0'
DESKTOP_UA = mozilla + '/5.0 (Windows NT 6.1; Win64; x64; rv:59.0) Gecko/20100101 Mobile ' + firefox + '/59.0'

# Base search url
SEARCH_URL = 'https://www.google.com/search?gbv=1&q='

user_config = json.load(open(STATIC_FOLDER + '/config.json'))


def get_ua(user_agent):
    return MOBILE_UA if ('Android' in user_agent or 'iPhone' in user_agent) else DESKTOP_UA


def send_request(curl_url, ua):
    request_header = []
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

    # Use :past(hour/day/week/month/year) if available
    # example search "new restaurants :past month"
    tbs = ''
    # if 'tbs' in request.args:
    #     tbs = '&tbs=' + request.args.get('tbs')
    #     q = q.replace(q.split(':past', 1)[-1], '').replace(':past', '')
    if ':past' in q:
        time_range = str.strip(q.split(':past', 1)[-1])
        tbs = '&tbs=qdr:' + str.lower(time_range[0])

    # Ensure search query is parsable
    q = urlparse.quote(q)

    # Pass along type of results (news, images, books, etc)
    tbm = ''
    if 'tbm' in request.args:
        tbm = '&tbm=' + request.args.get('tbm')

    # Get results page start value (10 per page, ie page 2 start val = 20)
    start = ''
    if 'start' in request.args:
        start = '&start=' + request.args.get('start')

    # Grab city from config, if available
    near = ''
    if 'near' in user_config:
        near = '&near=' + urlparse.quote(user_config['near'])

    user_agent = request.headers.get('User-Agent')
    full_query = q + tbs + tbm + start + near

    get_body = send_request(SEARCH_URL + full_query, get_ua(user_agent))

    # Aesthetic only re-skinning
    dark_mode = 'dark' in user_config and user_config['dark']
    get_body = get_body.replace('>G<', '>Sh<')
    pattern = re.compile('4285f4|ea4335|fbcc05|34a853|fbbc05', re.IGNORECASE)
    get_body = pattern.sub('685e79', get_body)
    if dark_mode:
        get_body = get_body.replace('fff', '000').replace('202124', 'ddd').replace('1967D2', '3b85ea')

    soup = BeautifulSoup(get_body, 'html.parser')

    # Remove all ads (TODO: Ad specific div classes probably change over time, look into a more generic method)
    main_divs = soup.find('div', {'id': 'main'})
    if main_divs is not None:
        ad_divs = main_divs.findAll('div', {'class': 'ZINbbc'}, recursive=False)
        sponsored_divs = main_divs.findAll('div', {'class': 'D1fz0e'}, recursive=False)
        for div in ad_divs + sponsored_divs:
            div.decompose()

    # Remove unnecessary button(s)
    for button in soup.find_all('button'):
        button.decompose()

    # Remove svg logos
    for svg in soup.find_all('svg'):
        svg.decompose()

    # Update logo
    logo = soup.find('a', {'class': 'l'})
    if logo is not None and ('Android' in user_agent or 'iPhone' in user_agent):
        logo.insert(0, 'Shoogle')
        logo['style'] = 'display: flex;justify-content: center;align-items: center;color: #685e79;font-size: 18px;'

    # Replace hrefs with only the intended destination (no "utm" type tags)
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/advanced_search' in href:
            a.decompose()
            continue

        if 'url?q=' in href:
            # Strip unneeded arguments
            href = urlparse.urlparse(href)
            href = parse_qs(href.query)['q'][0]

            # Add no-js option
            if 'nojs' in user_config and user_config['nojs']:
                nojs_link = soup.new_tag('a')
                nojs_link['href'] = '/window?location=' + href
                nojs_link['style'] = 'display:block;width:100%;'
                nojs_link.string = 'NoJS Link: ' + nojs_link['href']
                a.append(BeautifulSoup('<br><hr><br>', 'html.parser'))
                a.append(nojs_link)

    # Set up dark mode if active
    if dark_mode:
        soup.find('html')['style'] = 'scrollbar-color: #333 #111;'
        for input_element in soup.findAll('input'):
            input_element['style'] = 'color:#fff;'

    # Ensure no extra scripts passed through
    try:
        for script in soup('script'):
            script.decompose()
        soup.find('div', id='sfooter').decompose()
    except Exception:
        pass

    return render_template('display.html', query=urlparse.unquote(q), response=soup)


@app.route('/config', methods=['POST'])
def config():
    global user_config
    with open(STATIC_FOLDER + '/config.json', 'w') as config_file:
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
    app.run(debug=True, host='0.0.0.0')
