from app import app
from flask import request, redirect, Response, render_template
import os
import pycurl
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

    user_agent = request.headers.get('User-Agent')

    google_ua = DESKTOP_UA
    if 'Android' in user_agent or 'iPhone' in user_agent:
        google_ua = MOBILE_UA

    b_obj = BytesIO()
    crl = pycurl.Curl()
    crl.setopt(crl.URL, 'https://www.google.com/search?q=' + url_parse(q) + tbm)
    crl.setopt(crl.USERAGENT, google_ua)
    crl.setopt(crl.WRITEDATA, b_obj)
    crl.perform()
    crl.close()
    get_body = b_obj.getvalue()
    return render_template('search.html', response=get_body.decode("utf-8", 'ignore'))


@app.route('/url', methods=['GET'])
def url():
    q = request.args.get('q')
    if len(q) > 0 and 'http' in q:
        return redirect(q)
    else:
        return render_template('error.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
