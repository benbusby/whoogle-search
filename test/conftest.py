from app import app
from app.utils.session import generate_key
import pytest
import random

demo_config = {
    'near': random.choice(['Seattle', 'New York', 'San Francisco']),
    'dark': str(random.getrandbits(1)),
    'nojs': str(random.getrandbits(1)),
    'lang_interface': random.choice(app.config['LANGUAGES'])['value'],
    'lang_search': random.choice(app.config['LANGUAGES'])['value'],
    'country': random.choice(app.config['COUNTRIES'])['value']
}


@pytest.fixture
def client():
    with app.test_client() as client:
        with client.session_transaction() as session:
            session['uuid'] = 'test'
            session['key'] = app.enc_key
            session['config'] = {}
            session['auth'] = False
        yield client
