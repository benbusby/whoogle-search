from app import app
from app.models.endpoint import Endpoint

import json

from test.conftest import demo_config


def test_main(client):
    rv = client.get('/')
    assert rv._status_code == 200


def test_search(client):
    rv = client.get(f'/{Endpoint.search}?q=test')
    assert rv._status_code == 200


def test_feeling_lucky(client):
    # Bang at beginning of query
    rv = client.get(f'/{Endpoint.search}?q=!%20wikipedia')
    assert rv._status_code == 303
    assert rv.headers.get('Location').startswith('https://www.wikipedia.org')

    # Move bang to end of query
    rv = client.get(f'/{Endpoint.search}?q=github%20!')
    assert rv._status_code == 303
    assert rv.headers.get('Location').startswith('https://github.com')


def test_ddg_bang(client):
    # Bang at beginning of query
    rv = client.get(f'/{Endpoint.search}?q=!gh%20whoogle')
    assert rv._status_code == 302
    assert rv.headers.get('Location').startswith('https://github.com')

    # Move bang to end of query
    rv = client.get(f'/{Endpoint.search}?q=github%20!w')
    assert rv._status_code == 302
    assert rv.headers.get('Location').startswith('https://en.wikipedia.org')

    # Move bang to middle of query
    rv = client.get(f'/{Endpoint.search}?q=big%20!r%20chungus')
    assert rv._status_code == 302
    assert rv.headers.get('Location').startswith('https://www.reddit.com')

    # Ensure bang is case insensitive
    rv = client.get(f'/{Endpoint.search}?q=!GH%20whoogle')
    assert rv._status_code == 302
    assert rv.headers.get('Location').startswith('https://github.com')

    # Ensure bang without a query still redirects to the result
    rv = client.get(f'/{Endpoint.search}?q=!gh')
    assert rv._status_code == 302
    assert rv.headers.get('Location').startswith('https://github.com')


def test_custom_bang(client):
    # Bang at beginning of query
    rv = client.get(f'/{Endpoint.search}?q=!i%20whoogle')
    assert rv._status_code == 302
    assert rv.headers.get('Location').startswith('search?q=')


def test_config(client):
    rv = client.post(f'/{Endpoint.config}', data=demo_config)
    assert rv._status_code == 302

    rv = client.get(f'/{Endpoint.config}')
    assert rv._status_code == 200

    config = json.loads(rv.data)
    for key in demo_config.keys():
        assert config[key] == demo_config[key]

    # Test disabling changing config from client
    app.config['CONFIG_DISABLE'] = 1
    dark_mod = not demo_config['dark']
    demo_config['dark'] = dark_mod
    rv = client.post(f'/{Endpoint.config}', data=demo_config)
    assert rv._status_code == 403

    rv = client.get(f'/{Endpoint.config}')
    config = json.loads(rv.data)
    assert config['dark'] != dark_mod


def test_opensearch(client):
    rv = client.get(f'/{Endpoint.opensearch}')
    assert rv._status_code == 200
    assert '<ShortName>Whoogle</ShortName>' in str(rv.data)
