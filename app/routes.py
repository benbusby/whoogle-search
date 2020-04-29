from app import app
from app.filter import Filter
from app.request import Request, gen_query
from bs4 import BeautifulSoup
from cryptography.fernet import Fernet, InvalidToken
from flask import g, make_response, request, redirect, render_template, send_file
import io
import json
import os
import urllib.parse as urlparse

app.config['APP_ROOT'] = os.getenv('APP_ROOT', os.path.dirname(os.path.abspath(__file__)))
app.config['STATIC_FOLDER'] = os.getenv('STATIC_FOLDER', os.path.join(app.config['APP_ROOT'], 'static'))

user_config = json.load(open(app.config['STATIC_FOLDER'] + '/config.json'))


@app.before_request
def before_request_func():
    g.user_request = Request(request.headers.get('User-Agent'))


@app.route('/', methods=['GET'])
def index():
    bg = '#000' if 'dark' in user_config and user_config['dark'] else '#fff'
    return render_template('index.html', bg=bg, ua=g.user_request.modified_user_agent)


@app.route('/opensearch.xml', methods=['GET'])
def opensearch():
    url_root = request.url_root
    if url_root.endswith('/'):
        url_root = url_root[:-1]

    template = render_template('opensearch.xml', shoogle_url=url_root)
    response = make_response(template)
    response.headers['Content-Type'] = 'application/xml'
    return response


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'GET':
        q = request.args.get('q')
        try:
            q = Fernet(app.secret_key).decrypt(q.encode()).decode()
        except InvalidToken:
            pass
    else:
        q = request.form['q']

    if q is None or len(q) == 0:
        return render_template('error.html')

    user_agent = request.headers.get('User-Agent')
    mobile = 'Android' in user_agent or 'iPhone' in user_agent

    content_filter = Filter(mobile, user_config, secret_key=app.secret_key)
    full_query = gen_query(q, request.args, content_filter.near)
    get_body = g.user_request.send(query=full_query)

    shoogle_results = content_filter.reskin(get_body)
    formatted_results = content_filter.clean(BeautifulSoup(shoogle_results, 'html.parser'))

    return render_template('display.html', query=urlparse.unquote(q), response=formatted_results)


@app.route('/config', methods=['GET', 'POST'])
def config():
    global user_config
    if request.method == 'GET':
        return json.dumps(user_config)
    else:
        config_data = request.form.to_dict()
        with open(app.config['STATIC_FOLDER'] + '/config.json', 'w') as config_file:
            config_file.write(json.dumps(config_data, indent=4))
            config_file.close()

            user_config = config_data

        return redirect('/')


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


if __name__ == '__main__':
    app.run(debug=True)
