from app import app
from bs4 import BeautifulSoup
from flask import request, redirect, Response, render_template
import os
import pycurl
import re
from .url import url_parse
import urllib.parse as urlparse
from urllib.parse import parse_qs
from io import BytesIO

MOBILE_UA = os.environ.get('MOZ') + '/5.0 (Android 4.20; Mobile; rv:54.0) Gecko/54.0 ' + os.environ.get('FF') + '/54.0'
DESKTOP_UA = os.environ.get('MOZ') + '/5.0 (Windows NT 6.1; Win64; x64; rv:59.0) Gecko/20100101 Mobile ' + os.environ.get('FF') + '/59.0'

SEARCH_URL = 'https://www.google.com/search?gbv=1&q='

nojs = int(os.environ.get('NOJS'))


def get_ua(user_agent):
    return MOBILE_UA if ('Android' in user_agent or 'iPhone' in user_agent) else DESKTOP_UA


def send_request(url, ua):
    request_header = []

    # Update as an optional param
    # Todo: this doesn't seem to work
    ip = '64.22.92.48'
    request_header.append('CLIENT-IP: ' + ip)
    request_header.append('X-FORWARDED-FOR: ' + ip)

    b_obj = BytesIO()
    crl = pycurl.Curl()
    crl.setopt(crl.URL, url)
    crl.setopt(crl.USERAGENT, ua)
    crl.setopt(crl.HTTPHEADER, request_header)
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

    tbm = ''
    if 'tbm' in request.args:
        tbm = '&tbm=' + request.args.get('tbm')

    start = ''
    if 'start' in request.args:
        start = '&start=' + request.args.get('start')

    # Change to a config setting
    near = '&near=boulder'
    if 'near' in request.args:
        near = '&near=' + request.args.get('near')

    user_agent = request.headers.get('User-Agent')
    full_query = url_parse(q) + tbm + start + near

    get_body = send_request(SEARCH_URL + full_query, get_ua(user_agent))
    get_body = get_body.replace('>G<', '>Sh<')
    pattern = re.compile('4285f4|ea4335|fbcc05|34a853|fbbc05', re.IGNORECASE)
    get_body = pattern.sub('0000ff', get_body)

    soup = BeautifulSoup(get_body, 'html.parser')

    ad_divs = soup.find('div', {'id':'main'}).findAll('div', {'class':'ZINbbc'}, recursive=False)
    for div in ad_divs:
        div.decompose()

    for a in soup.find_all('a', href=True):
        href = a['href']
        if 'url?q=' in href:
            href = urlparse.urlparse(href)
            href = parse_qs(href.query)['q'][0]
        if nojs:
            a['href'] = '/window?location=' + href
        #else:
        #    a['href'] = 'about:reader?url=' + href
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
