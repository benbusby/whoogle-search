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

# Get Mozilla Firefox rhyme (important) and form a new user agent
mozilla = rhyme.get_rhyme('Mo') + 'zilla'
firefox = rhyme.get_rhyme('Fire') + 'fox'

MOBILE_UA = mozilla + '/5.0 (Android 4.20; Mobile; rv:54.0) Gecko/54.0 ' + firefox + '/59.0'
DESKTOP_UA = mozilla + '/5.0 (Windows NT 6.1; Win64; x64; rv:59.0) Gecko/20100101 Mobile ' + firefox + '/59.0'

# Base search url
SEARCH_URL = 'https://www.google.com/search?gbv=1&q='

# Optional nojs tag - opens links in a contained window with all js removed
# (can be useful for achieving nojs on mobile)
nojs = int(os.environ.get('NOJS'))

config = json.load(open('config.json'))


def get_ua(user_agent):
    return MOBILE_UA if ('Android' in user_agent or 'iPhone' in user_agent) else DESKTOP_UA


def send_request(curl_url, ua):
    request_header = []

    b_obj = BytesIO()
    crl = pycurl.Curl()
    crl.setopt(crl.URL, curl_url)
    crl.setopt(crl.USERAGENT, ua)
    crl.setopt(crl.WRITEDATA, b_obj)
    crl.perform()
    crl.close()

    return b_obj.getvalue().decode('utf-8', 'ignore')


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/search', methods=['GET'])
def search():
    q = request.args.get('q')
    if q is None or len(q) <= 0:
        return render_template('error.html')
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
    if 'near' in config:
        near = '&near=' + config['near']

    user_agent = request.headers.get('User-Agent')
    full_query = q + tbm + start + near

    # Aesthetic only re-skinning
    get_body = send_request(SEARCH_URL + full_query, get_ua(user_agent))
    get_body = get_body.replace('>G<', '>Sh<')
    pattern = re.compile('4285f4|ea4335|fbcc05|34a853|fbbc05', re.IGNORECASE)
    get_body = pattern.sub('685e79', get_body)

    soup = BeautifulSoup(get_body, 'html.parser')

    # Remove all ads (TODO: Ad specific div class may change over time, look into a more generic method)
    ad_divs = soup.find('div', {'id': 'main'}).findAll('div', {'class': 'ZINbbc'}, recursive=False)
    for div in ad_divs:
        div.decompose()

    # Remove unnecessary button(s)
    for button in soup.find_all('button'):
        button.decompose()

    # Replace hrefs with only the intended destination (no "utm" type tags)
    for a in soup.find_all('a', href=True):
        href = a['href']
        if 'url?q=' in href:
            href = urlparse.urlparse(href)
            href = parse_qs(href.query)['q'][0]
        if nojs:
            a['href'] = '/window?location=' + href
        # else: # Automatically go to reader mode in ff? Not sure if possible
        #    a['href'] = 'about:reader?url=' + href

    # Ensure no extra scripts passed through
    try:
        for script in soup("script"):
            script.decompose()
        soup.find('div', id='sfooter').decompose()
    except Exception:
        pass

    return render_template('display.html', response=soup)


@app.route('/url', methods=['GET'])
def url():
    if 'url' in request.args:
        return redirect(request.args.get('url'))

    q = request.args.get('q')
    if len(q) > 0 and 'http' in q:
        return redirect(q)
    else:
        return render_template('error.html')


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
