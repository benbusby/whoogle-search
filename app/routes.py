from app import app
from bs4 import BeautifulSoup
from flask import request, redirect, Response, render_template
import os
import pycurl
import re
from .url import url_parse
from io import BytesIO

MOBILE_UA = 'Mozilla/5.0 (Linux; Android 8.0.0; SM-G960F Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.84 Mobile Safari/537.36'
DESKTOP_UA = 'Brozilla/5.0 (Windows NT 6.1; Win64; x64; rv:59.0) Gecko/20100101 Mobile LizzieMcGuirefox/59.0'


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

    user_agent = request.headers.get('User-Agent')
    full_query = url_parse(q) + tbm + start

    google_ua = DESKTOP_UA
    if 'Android' in user_agent or 'iPhone' in user_agent:
        google_ua = MOBILE_UA

    b_obj = BytesIO()
    crl = pycurl.Curl()
    crl.setopt(crl.URL, 'https://www.google.com/search?gbv=1&q=' + full_query)
    crl.setopt(crl.USERAGENT, google_ua)
    crl.setopt(crl.WRITEDATA, b_obj)
    crl.perform()
    crl.close()
    get_body = b_obj.getvalue().decode('utf-8', 'ignore')
    get_body = get_body.replace('data-src', 'src').replace('.001', '1').replace('visibility:hidden', 'visibility:visible').replace('>G<', '>Bl<')

    pattern = re.compile('4285f4|ea4335|fbcc05|34a853|fbbc05', re.IGNORECASE)
    get_body = pattern.sub('0000ff', get_body)

    soup = BeautifulSoup(get_body, 'html.parser')
    try:
        for script in soup("script"):
            script.decompose()
        soup.find('div', id='sfooter').decompose()
    except Exception:
        pass

    return render_template('search.html', response=soup)


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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
