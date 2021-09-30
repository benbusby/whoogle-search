from app import app

import json

from test.conftest import demo_config


def test_main(client):
    rv = client.get('/')
    assert rv._status_code == 200


def test_search(client):
    rv = client.get('/search?q=test')
    assert rv._status_code == 200


def test_feeling_lucky(client):
    rv = client.get('/search?q=!%20test')
    assert rv._status_code == 303


def test_ddg_bang(client):
    # Bang at beginning of query
    rv = client.get('/search?q=!gh%20whoogle')
    assert rv._status_code == 302
    assert rv.headers.get('Location').startswith('https://github.com')

    # Move bang to end of query
    rv = client.get('/search?q=github%20!w')
    assert rv._status_code == 302
    assert rv.headers.get('Location').startswith('https://en.wikipedia.org')

    # Move bang to middle of query
    rv = client.get('/search?q=big%20!r%20chungus')
    assert rv._status_code == 302
    assert rv.headers.get('Location').startswith('https://www.reddit.com')

    # Ensure bang is case insensitive
    rv = client.get('/search?q=!GH%20whoogle')
    assert rv._status_code == 302
    assert rv.headers.get('Location').startswith('https://github.com')


def test_config(client):
    rv = client.post('/config', data=demo_config)
    assert rv._status_code == 302

    rv = client.get('/config')
    assert rv._status_code == 200

    config = json.loads(rv.data)
    for key in demo_config.keys():
        assert config[key] == demo_config[key]

    # Test setting config via search
    custom_config = '&dark=1&lang_interface=lang_en'
    rv = client.get('/search?q=test' + custom_config)
    assert rv._status_code == 200
    assert custom_config.replace('&', '&amp;') in str(rv.data)

    # Test disabling changing config from client
    app.config['CONFIG_DISABLE'] = 1
    dark_mod = not demo_config['dark']
    demo_config['dark'] = dark_mod
    rv = client.post('/config', data=demo_config)
    assert rv._status_code == 403

    rv = client.get('/config')
    config = json.loads(rv.data)
    assert config['dark'] != dark_mod


def test_opensearch(client):
    rv = client.get('/opensearch.xml')
    assert rv._status_code == 200
    assert '<ShortName>Whoogle</ShortName>' in str(rv.data)
