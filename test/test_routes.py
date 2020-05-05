import json
import random

demo_config = {
    'near': random.choice(['Seattle', 'New York', 'San Francisco']),
    'dark_mode': str(random.getrandbits(1)),
    'nojs': str(random.getrandbits(1))
}


def test_main(client):
    rv = client.get('/')
    assert rv._status_code == 200


def test_search(client):
    rv = client.get('/search?q=test')
    assert rv._status_code == 200


def test_config(client):
    rv = client.post('/config', data=demo_config)
    assert rv._status_code == 302

    rv = client.get('/config')
    assert rv._status_code == 200

    config = json.loads(rv.data)
    for key in demo_config.keys():
        assert config[key] == demo_config[key]


def test_opensearch(client):
    rv = client.get('/opensearch.xml')
    assert rv._status_code == 200
    assert 'Whoogle' in str(rv.data)
