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
    rv = client.get('/search?q=!gh%20whoogle')
    assert rv._status_code == 302
    assert rv.headers.get('Location').startswith('https://github.com')

    rv = client.get('/search?q=!w%20github')
    assert rv._status_code == 302
    assert rv.headers.get('Location').startswith('https://en.wikipedia.org')


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


def test_opensearch(client):
    rv = client.get('/opensearch.xml')
    assert rv._status_code == 200
    assert '<ShortName>Whoogle</ShortName>' in str(rv.data)
