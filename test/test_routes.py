import json
from test.conftest import client

demo_config = {
    'near': 'Seattle',
    'dark_mode': 0,
    'nojs': 0
}


def test_main(client):
    rv = client.get('/')
    assert rv._status_code == 200


def test_search(client):
    rv = client.get('/search?q=test')
    assert rv._status_code == 200


def test_config(client):
    rv = client.post('/config', data=json.dumps(demo_config))
    assert rv._status_code == 200

    rv = client.get('/config')
    assert rv._status_code == 200

    config = json.loads(rv.data)
    for key in demo_config.keys():
        assert config[key] == demo_config[key]
